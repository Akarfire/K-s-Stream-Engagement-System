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


class CommandProcessor:
    def __init__(self, InConfigController, InTTS):

        # Data initializing
        self.Commands = InConfigController.Commands
        for c in self.Commands:
            self.Commands[c].AssignProcessor(self)

        self.CommandCalls = {}
        self.CallLengths = set()

        self.LConfigController = InConfigController

        for com in self.Commands:
            for call in self.Commands[com].Calls:
                self.CommandCalls[call] = self.Commands[com].Name
                self.CallLengths.add(len(call))

        # Queue
        self.CommandQueue = queue.Queue()
        #self.QueueTimer = 0.0
        self.HasActiveCommand = False
        self.ActiveCommand = None

        # TTS
        self.TTS = InTTS


    def UpdateCommandExecution(self, DeltaTime):

        if not self.HasActiveCommand:
            if not self.CommandQueue.empty():
                QCommand = self.CommandQueue.get()

                self.ActiveCommand = self.Commands[QCommand.Command]
                self.ActiveCommand.ExecuteCommand(QCommand.Message)

                self.HasActiveCommand = True

        else:
            self.ActiveCommand.Update(DeltaTime)

        # if self.QueueTimer > 0 or (not self.CommandQueue.empty()):
        #
        #     self.QueueTimer -= DeltaTime
        #     print("Current Queue Time: ", self.QueueTimer)
        #
        #     if self.QueueTimer <= 0:
        #         self.QueueTimer = 0
        #
        #         if not self.CommandQueue.empty():
        #             QCommand = self.CommandQueue.get()
        #             Time = self.ExecuteCommand(QCommand)
        #
        #             # # Calculating waiting time
        #             # Time = 0.0
        #             # if "time" in self.Commands[QCommand.Command].Atr:
        #             #     Time = self.Commands[QCommand.Command].Atr["time"]
        #             #
        #             # elif "calc_time_msg_len" in self.Commands[QCommand.Command].Atr:
        #             #     TimeFactor = 0.1
        #             #     if "time_fac" in self.Commands[QCommand.Command].Atr:
        #             #         TimeFactor =self.Commands[QCommand.Command].Atr["time_fac"]
        #             #
        #             #     Time = len(QCommand.Message.Message) * TimeFactor
        #
        #             self.QueueTimer = Time

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



# # TEMPORARy
#     def ExecuteCommand(self, InQueuedCommand):
#
#         # Instructions aren't here yet, so hard coding goes brrrrrrrrrr
#         if InQueuedCommand.Command == "VOICE":
#             return Instructions.Command_TTS(self.TTS, InQueuedCommand.Message)
#
#         elif "sfx" in self.Commands[InQueuedCommand.Command].Atr:
#             Volume = 1.0
#             if "volume" in self.Commands[InQueuedCommand.Command].Atr:
#                 Volume = self.Commands[InQueuedCommand.Command].Atr["volume"]
#
#             if "file" in self.Commands[InQueuedCommand.Command].Atr:
#                 return Instructions.fCommand_PlaySound(self.TTS, "SFX/" + self.Commands[InQueuedCommand.Command].Atr["file"], Volume)
#
#             else:
#                 return Instructions.fCommand_PlaySound(self.TTS, "SFX/" + InQueuedCommand.Command + ".mp3", Volume)
#
#         return 0.0

