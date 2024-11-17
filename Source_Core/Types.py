from dataclasses import dataclass

@dataclass
class ChatMessage:
    Source : str
    Time : str
    Author: str
    Message: str

@dataclass
class TwitchAuthData:
    server : str
    port : int
    nickname : str
    token : str
    channel : str

@dataclass
class ObsAuthData:
    host : str
    port : int
    password : str


class DataMessage:
    def __init__(self, InReceiverAddress, InSenderAddress, InDataType, InData):
        self.ReceiverAddress = InReceiverAddress
        self.SenderAddress = InSenderAddress
        self.DataType = InDataType # "RE" - request, "CB" - callback, "EV" - event, "EVN" - event notification, "IN" - instruction
        self.Data = InData # {"Head" : "message name", "Data" : ...}


class Command:
    def __init__(self, InName, InCalls, InAtr):
        self.Name = InName
        self.Calls = InCalls
        self.Atr = InAtr
        self.Processor = None

        self.FinishOnTimer = True
        self.Timer = 0
        if "time" in self.Atr:
            self.Timer = self.Atr["time"]

    def AssignProcessor(self, InProcessor):
        self.Processor = InProcessor

    def Update(self, DeltaTime):
        if self.FinishOnTimer:
            self.Timer -= DeltaTime
            if self.Timer <= 0:
                self.FinishExecution()

    def ExecuteCommand(self, InChatMessage):
        pass

    def FinishExecution(self):
        self.Processor.OnCurrentCommandFinished()

    def OnProcessorReceivedEventNotification(self, InDataMessage):
        pass