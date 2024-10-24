from dataclasses import dataclass

import pytchat
import socket
import TextToSpeech as tts

@dataclass
class TwitchAuthData:
    server : str
    port : int
    nickname : str
    token : str
    channel : str

class ChatReader:
    def __init__(self, use_tts,  in_tts, use_yt, video_url, use_twitch, twitch_auth_data):

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

        # Twitch Chat
        if (use_twitch):
            self.Socket = socket.socket()
            self.Socket.connect((twitch_auth_data.server, twitch_auth_data.port))

            self.Socket.send(f"PASS {twitch_auth_data.token}\n".encode('utf-8'))
            self.Socket.send(f"NICK {twitch_auth_data.nickname}\n".encode('utf-8'))
            self.Socket.send(f"JOIN {twitch_auth_data.channel}\n".encode('utf-8'))

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
                    self.OnChatMessageArrived(c)

        # Twitch
        if self.USE_TWITCH:
            resp = self.Socket.recv(2048).decode('utf-8')


    def OnChatMessageArrived(self, message):
        print(f"{message.datetime} - {message.author.name}: {message.message}")

        if self.USE_TTS:
            FilteredMessage = self.FilterMessage(message.message)
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
