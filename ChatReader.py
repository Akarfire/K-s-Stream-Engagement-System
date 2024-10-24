from dataclasses import dataclass

import pytchat
import socket
import select
import datetime
import re

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
    def __init__(self, use_tts,  in_tts, use_yt, video_url, use_twitch, twitch_auth_data_file):

        self.USE_TTS = use_tts
        self.USE_YT = use_yt
        self.USE_TWITCH = use_twitch

        # Initial Info Print
        print(
            f"Using TTS: {use_tts}\nUsing YT: {use_yt}\nUsing Twitch: {use_twitch}\n\n "
        )

        # YT Chat
        if use_yt:
            self.Chat = pytchat.create(video_id=video_url)

        # Twitch Chat Data
        FileTwitchAuthData = open(twitch_auth_data_file)
        TwitchAuthDataRead = [str(i) for i in FileTwitchAuthData.readlines()]

        MyTwitchAuthData = TwitchAuthData(
            server="irc.chat.twitch.tv",
            port=6667,
            nickname=TwitchAuthDataRead[0],
            token=TwitchAuthDataRead[1],
            channel=TwitchAuthDataRead[2]
        )

        # Twitch Chat Connection
        if (use_twitch):
            self.TwitchSocket = socket.socket()
            self.TwitchSocket.connect((MyTwitchAuthData.server, MyTwitchAuthData.port))
            self.TwitchSocket.setblocking(0)

            self.TwitchSocket.send(f"PASS {MyTwitchAuthData.token}\n".encode('utf-8'))
            self.TwitchSocket.send(f"NICK {MyTwitchAuthData.nickname}\n".encode('utf-8'))
            self.TwitchSocket.send(f"JOIN {MyTwitchAuthData.channel}\n".encode('utf-8'))

        # TTS
        if use_tts:
            self.ReadTTS = in_tts

        # Filter Setup
        f = open("BanWords.txt")
        self.BanWordList = [i for w in f.readlines() for i in w.split()]
        f.close()


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


    def ParseYTMessage(self, inMessage):

        outMessage = ChatMessage("YT", "", "", "")

        outMessage.Time = inMessage.datetime
        outMessage.Author = inMessage.author.name
        outMessage.Message = inMessage.message

        return outMessage

    def ParseTwitchMessage(self, inMessage):

        outMessage = ChatMessage("Twitch", "", "", "")
        outMessage.Time = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")

        msg = inMessage.split("PRIVMSG")

        if len(msg) > 1:
            username, channel, message = re.search(':(.*)\!.*@.*\.tmi\.twitch\.tv PRIVMSG #(.*) :(.*)', inMessage).groups()

            outMessage.Author = username
            outMessage.Message = message

            return outMessage

        outMessage.Author = "Twitch"
        return outMessage


    def OnChatMessageArrived(self, message):
        print(f"{message.Time} - {message.Author}: {message.Message}")

        if self.USE_TTS and len(message.Message) > 0:
            FilteredMessage = self.FilterMessage(message.Message)
            self.ReadTTS.ConvertTTS(FilteredMessage)
            self.ReadTTS.PlayTTS()


    def FilterMessage(self, message):
        FILTERED = False

        for ban in self.BanWordList:
            if ban in message:
                FILTERED = True
                break

        if FILTERED:
            print("Message Filtered!")
            return "FILTERED"

        return message
