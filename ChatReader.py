import time
from dataclasses import dataclass

import pytchat
import socket
import select
import datetime
import re

from profanity_check import predict, predict_prob

from Types import ChatMessage, TwitchAuthData
from Commands import CommandProcessor

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
                    self.Chat = pytchat.create(video_id=InConfigController.YT_Url)
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


    def UpdateChat(self):
        # YT
        if self.USE_YT:
            if self.Chat.is_alive():
                for c in self.Chat.get().sync_items():
                    self.OnChatMessageArrived(self.ParseYTMessage(c))

        # Twitch
        if self.USE_TWITCH:
            Ready = select.select([self.TwitchSocket], [], [], 1)
            if Ready[0]:
                resp = self.TwitchSocket.recv(2048).decode('utf-8')

                if resp.startswith('PING'):
                    self.TwitchSocket.send("PONG\n".encode('utf-8'))

                elif len(resp) > 0:
                    self.OnChatMessageArrived(self.ParseTwitchMessage(resp))


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




