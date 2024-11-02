import queue
import Source.CommandInstructions as Instructions
# Source.Types import Command

class QueuedCommand:
    def __init__(self, InCommand, InChatMessage):
        self.Command = InCommand
        self.Message = InChatMessage


def AssignCommand(InName, InCalls, InAtr):

    if "sfx" in InAtr:
        return Instructions.Command_PlaySound(InName, InCalls, InAtr)

    elif InName == "VOICE":
        return Instructions.Command_TTS(InName, InCalls, InAtr)

# Actual Class

class CommandProcessor:
    def __init__(self, InConfigController, InTTS, InObsInterface):

        # Data initializing
        self.Commands = InConfigController.Commands
        for c in self.Commands:
            self.Commands[c].AssignProcessor(self)

        self.CommandCalls = {}
        self.CallLengths = set()

        # Object Pointers
        self.LConfigController = InConfigController
        self.TTS = InTTS
        self.LObsInterface = InObsInterface

        # Processing Commands
        for com in self.Commands:
            for call in self.Commands[com].Calls:
                self.CommandCalls[call] = self.Commands[com].Name
                self.CallLengths.add(len(call))

        # Queue
        self.CommandQueue = queue.Queue()
        self.HasActiveCommand = False
        self.ActiveCommand = None


    def UpdateCommandExecution(self, DeltaTime):

        if not self.HasActiveCommand:
            if not self.CommandQueue.empty():
                QCommand = self.CommandQueue.get()

                self.ActiveCommand = self.Commands[QCommand.Command]
                self.ActiveCommand.ExecuteCommand(QCommand.Message)

                self.HasActiveCommand = True

        else:
            self.ActiveCommand.Update(DeltaTime)


    def OnCurrentCommandFinished(self):
        self.HasActiveCommand = False


    def ScanAndExecuteMessageCommands(self, InChatMessage, InWasFiltered):
        Commands, CleanMessage = self.ScanMessageForCommands(InChatMessage.Message)
        NewChatMessage = InChatMessage
        NewChatMessage.Message = CleanMessage

        if InWasFiltered:
            NewChatMessage.Message = "FILTERED"

        Priorities = list(Commands.keys())
        Priorities.sort()

        for p in Priorities:
            for com in Commands[p]:
                self.CommandQueue.put(QueuedCommand(com, NewChatMessage))


    def ScanMessageForCommands(self, Message):
        OutMessage = Message

        if Message.count('!') < 2:
            return {}, Message

        Segments = Message.split('!')
        MsgCommands = {}
        AllFoundCommands = set()

        for seg in Segments:
            pseg = seg.replace(' ', '').upper()
            if (pseg in AllFoundCommands) or (len(pseg) in self.CallLengths and pseg in self.CommandCalls):

                if not ((pseg in AllFoundCommands) and ("once_per_message" in self.Commands[self.CommandCalls[pseg]].Atr)):
                    Priority = 0
                    if "priority" in self.Commands[self.CommandCalls[pseg]].Atr:
                        Priority = self.Commands[self.CommandCalls[pseg]].Atr["priority"]

                    if Priority in MsgCommands:
                        MsgCommands[Priority].append(self.CommandCalls[pseg])

                    else:
                        MsgCommands[Priority] = [self.CommandCalls[pseg]]

                    AllFoundCommands.add(pseg)

                OutMessage = OutMessage.replace('!' + seg + '!', '')

        return MsgCommands, OutMessage


