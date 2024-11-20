from dataclasses import dataclass

@dataclass
class ChatMessage:
    Source : str
    Time : str
    Author: str
    Message: str


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


