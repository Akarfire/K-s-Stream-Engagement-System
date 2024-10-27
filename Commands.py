from Types import Command, ChatMessage
from Config import ConfigController
import queue
import CommandInstructions as Instructions

class QueuedCommand:
    def __init__(self, InCommand, InChatMessage):
        self.Command = InCommand
        self.Message = InChatMessage

class CommandProcessor:
    def __init__(self, InConfigController, InTTS):

        # Data initializing
        self.Commands = InConfigController.Commands
        self.CommandCalls = {}
        self.CallLengths = set()

        for com in self.Commands:
            for call in self.Commands[com].Calls:
                self.CommandCalls[call] = self.Commands[com].Name
                self.CallLengths.add(len(call))

        # Queue
        self.CommandQueue = queue.Queue()
        self.QueueTimer = 0.0

        # TTS
        self.TTS = InTTS


    def UpdateCommandExecution(self, DeltaTime):

        if self.QueueTimer > 0 or (not self.CommandQueue.empty()):

            self.QueueTimer -= DeltaTime
            #print("Current Queue Time: ", self.QueueTimer)

            if self.QueueTimer <= 0:
                self.QueueTimer = 0

                if not self.CommandQueue.empty():
                    QCommand = self.CommandQueue.get()
                    self.ExecuteCommand(QCommand)

                    # Calculating waiting time
                    Time = 0.0
                    if "time" in self.Commands[QCommand.Command].Atr:
                        Time = self.Commands[QCommand.Command].Atr["time"]

                    elif "calc_time_msg_len" in self.Commands[QCommand.Command].Atr:
                        TimeFactor = 0.1
                        if "time_fac" in self.Commands[QCommand.Command].Atr:
                            TimeFactor =self.Commands[QCommand.Command].Atr["time_fac"]

                        Time = len(QCommand.Message.Message) * TimeFactor

                    self.QueueTimer = Time


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



# TEMPORARy
    def ExecuteCommand(self, InQueuedCommand):

        # Instructions aren't here yet, so hard coding goes brrrrrrrrrr
        if InQueuedCommand.Command == "VOICE":
            Instructions.Command_TTS(self.TTS, InQueuedCommand.Message)

        elif "sfx" in self.Commands[InQueuedCommand.Command].Atr:

            if "file" in self.Commands[InQueuedCommand.Command].Atr:
                Instructions.Command_PlaySound(self.TTS, "SFX/" + self.Commands[InQueuedCommand.Command].Atr["file"])

            else:
                Instructions.Command_PlaySound(self.TTS, "SFX/" + InQueuedCommand.Command + ".mp3")
