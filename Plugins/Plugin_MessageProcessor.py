from Source_Core import PluginImpl
from profanity_check import predict_prob
from Source_Core.Types import ChatMessage

class MessageProcessor(PluginImpl.PluginBase):

    def __init__(self):
        super().__init__()
        self.Address = "MessageProcessor"
        self.ConfigSection = "MessageProcessor"
        self.Subscriptions = ["OnChatMessageArrived"]
        self.Instructions = []


    def InitPlugin(self, InPluginManager):
        super().InitPlugin(InPluginManager)

        # Initial Info Print
        self.MyPluginManager.LLogger.LogStatus(
            f"YouTube Chat Reader Plugin Initiated!"
        )


    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):
        pass

    def ReceiveMessage(self, InDataMessage):

        super().ReceiveMessage(InDataMessage)
        if InDataMessage.Data["Head"] == "OnChatMessageArrived":
            self.OnChatMessageArrived(InDataMessage.Data["Data"])


    def OnChatMessageArrived(self, Message):
        self.MyPluginManager.LLogger.LogMessage(Message)

        NewMessage = Message
        NewMessage.Message, WasFiltered = self.FilterMessage(Message.Message)

        #self.MyPluginManager.MyCore.MyCommandProcessor.ScanAndExecuteMessageCommands(NewMessage, WasFiltered)
        self.TransmitInstruction("COMMAND_ProcessMessageCommands", {"Message" : NewMessage, "WasFiltered" : WasFiltered})


    def FilterMessage(self, Message):

        #self.LConfigController.Options["Filter_Tolerance"]
        FILTERED = predict_prob([Message])[0] > 0.85

        if FILTERED:
            self.MyPluginManager.LLogger.LogStatus("Message Filtered!")
            return Message, True

        return Message, False

