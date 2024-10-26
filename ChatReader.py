import time
from dataclasses import dataclass

import pytchat
import socket
import select
import datetime
import re

from profanity_check import predict, predict_prob

@dataclass
class TwitchAuthData:
    server : str
    port : int
    nickname : str
    token : str
    channel : str

@dataclass
class ChatMessage:
    Source : str
    Time : str
    Author: str
    Message: str

class ChatReader:
    def __init__(self, ConfigController, InTTS):

        self.USE_YT = ConfigController.Options["Use_YT"] and ConfigController.YT_DataFound
        self.USE_TWITCH = ConfigController.Options["Use_Twitch"] and ConfigController.TWITCH_DataFound

        # Initial Info Print
        print(
            f"Using YT: {self.USE_YT}\nUsing Twitch: {self.USE_TWITCH}\n\n "
        )

        # YT Chat
        if self.USE_YT:
            IsYTChatRunning = False
            while not IsYTChatRunning:
                try:
                    self.Chat = pytchat.create(video_id=ConfigController.YT_Url)
                    IsYTChatRunning = True

                except:
                    print("Failed to connect to YT, attempting reconnection in 1 second")
                    time.sleep(1)
                    pass


        # Twitch Chat Connection
        if (self.USE_TWITCH):

            try:
                self.TwitchSocket = socket.socket()
                self.TwitchSocket.connect((ConfigController.TwitchAuth.server, ConfigController.TwitchAuth.port))
                self.TwitchSocket.setblocking(False)

                self.TwitchSocket.send(f"PASS {ConfigController.TwitchAuth.token}\n".encode('utf-8'))
                self.TwitchSocket.send(f"NICK {ConfigController.TwitchAuth.nickname}\n".encode('utf-8'))
                self.TwitchSocket.send(f"JOIN {ConfigController.TwitchAuth.channel}\n".encode('utf-8'))

            except:
                print("Failed to connect to TWITCH!")

        # TTS
        self.ReadTTS = InTTS

        # TEMPORARY COMMAND LIST
        self.CommandList = ["!VOICE!", "!SUS!", "!WOW!", "!CLOCK!", "!TO_BE_CONTINUED!", "!COIN!"]


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
        ActualMessage, Commands = self.ScanMessageForCommands(Message.Message)

        print(f"{Message.Time} - {Message.Author}: {ActualMessage}")
        if len(Commands) > 0:
            print(Commands)

        # TEMPORARY COMMAND PROCESSING
        if "!VOICE!" in Commands:
            self.Command_TTSMessage(ActualMessage)

        if "!SUS!" in Commands:
            self.Command_PlaySound("SFX/Among Us Impostor.mp3")

        if "!WOW!" in Commands:
            self.Command_PlaySound("SFX/WOW (OWEN WILSON).mp3")

        if "!CLOCK!" in Commands:
            self.Command_PlaySound("SFX/CLOCK TICKING.mp3")

        if "!TO_BE_CONTINUED!" in Commands:
            self.Command_PlaySound("SFX/TO BE CONTINUED.mp3")

        if "!COIN!" in Commands:
            self.Command_PlaySound("SFX/8bit_CoinPickUp13.wav")



    def FilterMessage(self, Message):

        FILTERED = predict([Message])[0]

        if FILTERED:
            print("Message Filtered!")
            return "FILTERED"

        return Message


    def ScanMessageForCommands(self, Message):
        Commands = []

        outMessage = Message

        if Message.count('!') > 1:
            for i in self.CommandList:
                if i in outMessage:
                    Commands.append(i)
                    outMessage = outMessage.replace(i, '')

        return outMessage, Commands


    def Command_TTSMessage(self, Message):
        if len(Message) > 0:
            FilteredMessage = self.FilterMessage(Message)

            self.ReadTTS.ConvertTTS(FilteredMessage)
            self.ReadTTS.PlayTTS()

    def Command_PlaySound(self, sound_file):
        self.ReadTTS.PlaySound(sound_file)



