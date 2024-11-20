import time
from queue import Queue
import socket
import select
import datetime
import re
import threading
from Source_Core.Types import ChatMessage, DataMessage
from Source_Core import PluginImpl
from dataclasses import dataclass

@dataclass
class TwitchAuthData:
    server : str
    port : int
    nickname : str
    token : str
    channel : str


class TwitchChatReader(PluginImpl.PluginBase):

    def __init__(self, InPluginManager):
        super().__init__(InPluginManager)
        self.Address = "TwitchChatReader"
        self.ConfigSection = "TwitchChat"
        self.Subscriptions = []
        self.Instructions = []

        self.TwitchAuth = TwitchAuthData("", 0, "", "", "")
        self.TWITCH_DataFound = False

        self.AddOption("Use_Twitch", True)
        self.AddOption("Chat_Fetch_Frequency", 8)


    def InitPlugin(self):
        super().InitPlugin()

        self.MyCore = self.MyPluginManager.MyCore

        self.USE_TWITCH = self.GetOption("Use_Twitch") and self.TWITCH_DataFound

        # Logger
        self.LLogger = self.MyCore.MyLogger

        # Initial Info Print
        self.LLogger.LogStatus(
            f"Twitch Chat Reader Plugin Initiated!\nUsing Twitch: {self.USE_TWITCH}\n "
        )

        # Twitch Chat Connection
        if self.USE_TWITCH:

            try:
                self.TwitchSocket = socket.socket()
                self.TwitchSocket.connect((self.TwitchAuth.server, self.TwitchAuth.port))
                self.TwitchSocket.setblocking(False)

                self.TwitchSocket.send(f"PASS {self.TwitchAuth.token}\n".encode('utf-8'))
                self.TwitchSocket.send(f"NICK {self.TwitchAuth.nickname}\n".encode('utf-8'))
                self.TwitchSocket.send(f"JOIN {self.TwitchAuth.channel}\n".encode('utf-8'))

            except Exception as e:
                self.LLogger.LogError("Failed to connect to TWITCH! : " + str(e))

        # Async
        self.TwitchFetchThread = threading.Thread(target=AsyncUpdateTwitch, args=(self,), daemon=True)

        self.TwitchFetchThread.start()

        # Message Queue
        self.MessageQueue = Queue()


    def DeletePlugin(self):
        self.TwitchSocket.close()


    def UpdatePlugin(self, DeltaSeconds):

        if not self.MessageQueue.empty():
            self.TransmitEvent("OnChatMessageArrived", self.MessageQueue.get())


    def ReceiveMessage(self, InDataMessage):
        super().ReceiveMessage(InDataMessage)


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

    def ReadConfigData(self, InConfigFileLines):

        self.ReadOptions(InConfigFileLines)

        Path = "Config/TWITCH_AUTH.txt"
        self.LLogger.LogStatus("Reading Twitch data at: " + Path)

        try:
            FileTwitchAuthData = open(Path)
            DataFound = True

        except:
            self.LLogger.LogStatus(f"'{Path}' doesn't exist, creating now")
            FileTwitchAuthData = open(Path, 'w')
            FileTwitchAuthData.write(
                "nickname: \n\
                token: \n\
                channel: ".replace('    ', '')
            )
            FileTwitchAuthData.close()

            DataFound = False
            pass

        if DataFound:
            TwitchData = FileTwitchAuthData.readlines()

            if len(TwitchData) >= 3:
                self.TwitchAuth = TwitchAuthData(
                    server="irc.chat.twitch.tv",
                    port=6667,
                    nickname=TwitchData[0].replace('nickname: ', ''),
                    token=TwitchData[1].replace('token: ', ''),
                    channel=TwitchData[2].replace('channel: ', '')
                )
                FileTwitchAuthData.close()

                self.TWITCH_DataFound = True

        else:
            self.LLogger.LogError("Twitch Data cannot be read, pls check the config file!")


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
                    InChatReader.MessageQueue.put(InChatReader.ParseTwitchMessage(resp))

        time.sleep(1 / InChatReader.GetOption("Chat_Fetch_Frequency"))