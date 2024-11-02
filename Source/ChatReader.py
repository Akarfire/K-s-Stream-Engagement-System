import time
import pytchat
import socket
import select
import datetime
import re

import threading

from profanity_check import predict_prob
from Source.Types import ChatMessage


class ChatReader:
    def __init__(self, InConfigController, InCommandProcessor):

        self.USE_YT = InConfigController.Options["Use_YT"] and InConfigController.YT_DataFound
        self.USE_TWITCH = InConfigController.Options["Use_Twitch"] and InConfigController.TWITCH_DataFound

        # Initial Info Print
        print(
            f"Using YT: {self.USE_YT}\nUsing Twitch: {self.USE_TWITCH}\n\n "
        )

        # YT Chat
        if self.USE_YT:
            IsYTChatRunning = False
            while not IsYTChatRunning:
                try:
                    self.YTChat = pytchat.create(video_id=InConfigController.YT_Url)
                    IsYTChatRunning = True

                except:
                    print("Failed to connect to YT, attempting reconnection in 1 second")
                    time.sleep(1)
                    pass


        # Twitch Chat Connection
        if (self.USE_TWITCH):

            try:
                self.TwitchSocket = socket.socket()
                self.TwitchSocket.connect((InConfigController.TwitchAuth.server, InConfigController.TwitchAuth.port))
                self.TwitchSocket.setblocking(False)

                self.TwitchSocket.send(f"PASS {InConfigController.TwitchAuth.token}\n".encode('utf-8'))
                self.TwitchSocket.send(f"NICK {InConfigController.TwitchAuth.nickname}\n".encode('utf-8'))
                self.TwitchSocket.send(f"JOIN {InConfigController.TwitchAuth.channel}\n".encode('utf-8'))

            except:
                print("Failed to connect to TWITCH!")

        # Config Controller
        self.LConfigController = InConfigController

        # Command Processor
        self.LCommandProcessor = InCommandProcessor

        # Async
        self.YTFetchThread = threading.Thread(target=AsyncUpdateYT, args=(self,), daemon=True)
        self.TwitchFetchThread = threading.Thread(target=AsyncUpdateTwitch, args=(self,), daemon=True)

        self.YTFetchThread.start()
        self.TwitchFetchThread.start()


    def __del__(self):
        self.TwitchSocket.close()
        self.YTChat.terminate()


    def ParseYTMessage(self, InMessage):

        outMessage = ChatMessage("YT", "", "", "")

        outMessage.Time = InMessage.datetime
        outMessage.Author = InMessage.author.name
        outMessage.Message = InMessage.message

        return outMessage


    def ParseTwitchMessage(self, InMessage):

        outMessage = ChatMessage("Twitch", "", "", "")
        outMessage.Time = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")

        msg = InMessage.split("PRIVMSG")

        if len(msg) > 1:
            username, channel, message = re.search(':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', InMessage).groups()

            outMessage.Author = username
            outMessage.Message = message

            return outMessage

        outMessage.Author = "Twitch"
        return outMessage


    def OnChatMessageArrived(self, Message):
        print(f"{Message.Time} - {Message.Author}: {Message.Message}")

        NewMessage = Message
        NewMessage.Message, WasFiltered = self.FilterMessage(Message.Message)

        self.LCommandProcessor.ScanAndExecuteMessageCommands(NewMessage, WasFiltered)


    def FilterMessage(self, Message):

        FILTERED = predict_prob([Message])[0] > self.LConfigController.Options["Filter_Tolerance"]

        if FILTERED:
            print("Message Filtered!")
            return Message, True

        return Message, False



# Async method for fetching chat
def AsyncUpdateYT(InChatReader):

    while True:
        # YT
        if InChatReader.USE_YT:
            if InChatReader.YTChat.is_alive():
                for c in InChatReader.YTChat.get().sync_items():
                    InChatReader.OnChatMessageArrived(InChatReader.ParseYTMessage(c))

            else:
                print("YT chat's down!")

        time.sleep(1 / InChatReader.LConfigController.Options["Chat_Fetch_Frequency"])


def AsyncUpdateTwitch(InChatReader):

    while True:
        # Twitch
        if InChatReader.USE_TWITCH:
            Ready = select.select([InChatReader.TwitchSocket], [], [], 1)
            if Ready[0]:
                resp = InChatReader.TwitchSocket.recv(2048).decode('utf-8')

                if resp.startswith('PING'):
                    InChatReader.TwitchSocket.send("PONG\n".encode('utf-8'))

                elif len(resp) > 0:
                    InChatReader.OnChatMessageArrived(InChatReader.ParseTwitchMessage(resp))

        time.sleep(1 / InChatReader.LConfigController.Options["Chat_Fetch_Frequency"])