from Types import Command
from Config import ConfigController

class CommandProcessor:
    def __init__(self, InConfigController):
        self.Commands = InConfigController.Commands

        self.CommandCalls = {}
        self.CallLengths = set()

        for com in self.Commands:
            for call in self.Commands[com].Calls:
                self.CommandCalls[call] = self.Commands[com].Name
                self.CallLengths.add(len(call))


    def ScanMessageForCommands(self, Message):
        OutMessage = Message

        Segments = Message.split('!')
        MsgCommands = []

        for seg in Segments:
            pseg = seg.replace(' ', '').upper()
            if len(pseg) in self.CallLengths and pseg in self.CommandCalls:
                MsgCommands.append(self.CommandCalls[pseg])

                OutMessage = OutMessage.replace('!' + seg + '!', '')

        return MsgCommands, OutMessage

