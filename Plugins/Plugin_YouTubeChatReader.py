import time
from queue import Queue
import pytchat
import socket
import select
import datetime
import re
import threading
from profanity_check import predict_prob
from Source_Core.Types import ChatMessage
from Source_Core import PluginImpl

class YTChatReader(PluginImpl.PluginBase):

    def __init__(self, InPluginManager):
        super().__init__(InPluginManager, "Init PLUGIN: YouTube Chat Reader")
        self.Address = "YTChatReader"
        self.ConfigSection = "YTChat"
        self.Subscriptions = []
        self.Instructions = []

        self.YT_Url = ""
        self.YT_DataFound = False
        self.ChatsDown = False

        self.AddOption("Use_YT", True)
        self.AddOption("Chat_Fetch_Frequency", 8)


    def InitPlugin(self):
        super().InitPlugin()

        self.USE_YT = self.GetOption("Use_YT") and self.YT_DataFound

        # Initial Info Print
        self.LLogger.LogStatus(
            f"YouTube Chat Reader Plugin Initiated!\nUsing YT: {self.USE_YT}\n"
        )

        # YT Chat
        if self.USE_YT:
            IsYTChatRunning = False
            while not IsYTChatRunning:
                try:
                    self.YTChat = pytchat.create(video_id=self.YT_Url)
                    IsYTChatRunning = True

                except Exception as e:
                    self.LLogger.LogError("Failed to connect to YT, attempting reconnection in 1 second: " + str(e))
                    time.sleep(1)
                    pass

        # Async
        self.YTFetchThread = threading.Thread(target=AsyncUpdateYT, args=(self,), daemon=True)

        self.YTFetchThread.start()
        # Message Queue
        self.MessageQueue = Queue()


    def DeletePlugin(self):
        self.YTChat.terminate()


    def UpdatePlugin(self, DeltaSeconds):

        if self.ChatsDown:
            self.ReconnectToYTChat()

        elif not self.MessageQueue.empty():
            self.TransmitEvent("OnChatMessageArrived", self.MessageQueue.get())

    def ReceiveMessage(self, InDataMessage):
        super().ReceiveMessage(InDataMessage)


    def ParseYTMessage(self, InMessage):

        outMessage = ChatMessage("YT", "", "", "")

        outMessage.Time = InMessage.datetime
        outMessage.Author = InMessage.author.name
        outMessage.Message = InMessage.message

        return outMessage


    def ReadConfigData(self, InConfigFileLines):
        self.ReadOptions(InConfigFileLines)

        Path = "Config/YT_URL.txt"
        self.LLogger.LogStatus("Reading YT data at: " + Path)
        try:
            YtUrlFile = open(Path)
            DataFound = True

        except:
            self.LLogger.LogStatus(f"'{Path}' doesn't exist, creating now")
            YtUrlFile = open(Path, 'w')
            YtUrlFile.write("YT_url: ")
            YtUrlFile.close()

            DataFound = False
            pass

        if DataFound:
            YTData = YtUrlFile.readlines()
            if len(YTData) > 0:
                self.YT_Url = YTData[0].replace("YT_url: ", '')

            YtUrlFile.close()

            self.YT_DataFound = True

        else:
            self.LLogger.LogError("YouTube Data cannot be read, pls check the config file!")


    def ReconnectToYTChat(self):

        self.YTChat.terminate()
        try:
            self.YTChat = pytchat.create(video_id=self.YT_Url)
            self.ChatsDown = False

        except Exception as e:
            self.LLogger.LogError("Failed to connect to YT, attempting reconnection in 1 second: " + str(e))
            self.ChatsDown = True
            pass



# Async method for fetching chat
def AsyncUpdateYT(InChatReader):

    while True:
        # YT
        if InChatReader.USE_YT:
            if InChatReader.YTChat.is_alive():
                for c in InChatReader.YTChat.get().sync_items():
                    InChatReader.MessageQueue.put(InChatReader.ParseYTMessage(c))

            else:
                InChatReader.LLogger.LogError("YT chat's down, attempting to reconnect!")
                InChatReader.ChatsDown = True

        time.sleep(1 / InChatReader.GetOption("Chat_Fetch_Frequency"))