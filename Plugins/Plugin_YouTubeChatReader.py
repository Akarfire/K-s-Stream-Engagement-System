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

    def __init__(self):
        super().__init__()

    def InitPlugin(self, InPluginManager):
        super().InitPlugin(InPluginManager)

        self.USE_YT = self.MyCore.MyConfigController.Options["Use_YT"] and self.MyCore.MyConfigController.YT_DataFound

        # Logger
        self.LLogger = self.MyCore.MyLogger
        self.LLogger.NewLogSegment("Init Chat Reader")

        # Initial Info Print
        self.LLogger.LogStatus(
            f"\nYouTube Chat Reader Plugin Initiated!\nUsing YT: {self.USE_YT}\n\n "
        )

        # YT Chat
        if self.USE_YT:
            IsYTChatRunning = False
            while not IsYTChatRunning:
                try:
                    self.YTChat = pytchat.create(video_id=self.MyCore.MyConfigController.YT_Url)
                    IsYTChatRunning = True

                except Exception as e:
                    self.LLogger.LogError("Failed to connect to YT, attempting reconnection in 1 second: " + str(e))
                    time.sleep(1)
                    pass

        # Config Controller
        self.LConfigController = self.MyCore.MyConfigController

        # Command Processor
        self.LCommandProcessor = self.MyCore.MyCommandProcessor

        # Async
        self.YTFetchThread = threading.Thread(target=AsyncUpdateYT, args=(self,), daemon=True)

        self.YTFetchThread.start()
        # Message Queue
        self.MessageQueue = Queue()


    def DeletePlugin(self):
        self.YTChat.terminate()


    def UpdatePlugin(self, DeltaSeconds):
        if not self.MessageQueue.empty():
            self.OnChatMessageArrived(self.MessageQueue.get())

    def ReceiveRequest(self, DataMessage):
        pass


    def ParseYTMessage(self, InMessage):

        outMessage = ChatMessage("YT", "", "", "")

        outMessage.Time = InMessage.datetime
        outMessage.Author = InMessage.author.name
        outMessage.Message = InMessage.message

        return outMessage


# Async method for fetching chat
def AsyncUpdateYT(InChatReader):

    while True:
        # YT
        if InChatReader.USE_YT:
            if InChatReader.YTChat.is_alive():
                for c in InChatReader.YTChat.get().sync_items():
                    InChatReader.MessageQueue.put(InChatReader.ParseYTMessage(c))

            else:
                InChatReader.LLogger.LogError("YT chat's down!")

        time.sleep(1 / InChatReader.LConfigController.Options["Chat_Fetch_Frequency"])