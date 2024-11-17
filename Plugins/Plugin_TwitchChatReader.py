import time
from queue import Queue
import socket
import select
import datetime
import re
import threading
from Source_Core.Types import ChatMessage, DataMessage
from Source_Core import PluginImpl

class TwitchChatReader(PluginImpl.PluginBase):

    def __init__(self):
        super().__init__()
        pass

    def InitPlugin(self, InPluginManager):
        super().InitPlugin(InPluginManager)

        self.MyCore = self.MyPluginManager.MyCore

        self.USE_TWITCH = self.MyCore.MyConfigController.Options["Use_Twitch"] and self.MyCore.MyConfigController.TWITCH_DataFound

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
                self.TwitchSocket.connect((self.MyCore.MyConfigController.TwitchAuth.server, self.MyCore.MyConfigController.TwitchAuth.port))
                self.TwitchSocket.setblocking(False)

                self.TwitchSocket.send(f"PASS {self.MyCore.MyConfigController.TwitchAuth.token}\n".encode('utf-8'))
                self.TwitchSocket.send(f"NICK {self.MyCore.MyConfigController.TwitchAuth.nickname}\n".encode('utf-8'))
                self.TwitchSocket.send(f"JOIN {self.MyCore.MyConfigController.TwitchAuth.channel}\n".encode('utf-8'))

            except Exception as e:
                self.LLogger.LogError("Failed to connect to TWITCH! : " + str(e))

        # Config Controller
        self.LConfigController = self.MyCore.MyConfigController

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
        pass


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

        time.sleep(1 / InChatReader.LConfigController.Options["Chat_Fetch_Frequency"])