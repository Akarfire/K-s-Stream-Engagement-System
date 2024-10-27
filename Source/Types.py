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

class Command:
    def __init__(self, InName, InCalls, InAtr):
        self.Name = InName
        self.Calls = InCalls
        self.Atr = InAtr