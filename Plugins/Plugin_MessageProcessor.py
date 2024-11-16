from Source_Core import PluginImpl
from profanity_check import predict_prob

class MessageProcessor(PluginImpl.PluginBase):

    def __init__(self):
        super().__init__()
        pass

    def InitPlugin(self, InPluginManager):
        super().InitPlugin(InPluginManager)
        self.Address = "MessageProcessor"

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):
        pass

    def ReceiveRequest(self, DataMessage):
        pass


    def OnChatMessageArrived(self, Message):
        self.MyPluginManager.LLogger.LogMessage(Message)

        NewMessage = Message
        NewMessage.Message, WasFiltered = self.FilterMessage(Message.Message)

        self.MyPluginManager.MyCore.MyCommandProcessor.ScanAndExecuteMessageCommands(NewMessage, WasFiltered)


    def FilterMessage(self, Message):

        #self.LConfigController.Options["Filter_Tolerance"]
        FILTERED = predict_prob([Message])[0] > 0.85

        if FILTERED:
            self.MyPluginManager.LLogger.LogStatus("Message Filtered!")
            return Message, True

        return Message, False

