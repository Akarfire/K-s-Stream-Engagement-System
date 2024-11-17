from Source_Core import PluginImpl
import queue
from Source_Core.Types import Command
from Source_Core.Types import DataMessage


class QueuedCommand:
    def __init__(self, InCommand, InChatMessage):
        self.Command = InCommand
        self.Message = InChatMessage


class CommandProcessor(PluginImpl.PluginBase):

    def __init__(self):
        super().__init__()

        self.LLogger = None

        self.Commands = dict()
        self.CommandCalls = {}
        self.CallLengths = set()

        # Queue
        self.CommandQueue = queue.Queue()
        self.HasActiveCommand = False
        self.ActiveCommand = None


    def InitPlugin(self, InPluginManager):
        super().InitPlugin(InPluginManager)
        self.Subscriptions = ["TTS_FinishedPlayingSFX", "TTS_FinishedPlayingTTS"]
        self.Instructions = ["COMMAND_ProcessMessageCommands"]

        self.LLogger = self.MyCore.MyLogger
        self.LLogger.NewLogSegment("Init Command Processor")

        # Data initializing
        self.TransmitMessage("Config", "RE", {"Head" : "Request_CommandList" , "Data" : None})


    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):

        if not self.HasActiveCommand:
            if not self.CommandQueue.empty():
                QCommand = self.CommandQueue.get()
                self.LLogger.LogStatus(
                    "COMMAND: Executing Queued command: " + QCommand.Command + " - Queue Len: " + str(self.CommandQueue.qsize()),
                    False)

                self.ActiveCommand = self.Commands[QCommand.Command]
                self.ActiveCommand.ExecuteCommand(QCommand.Message)

                self.HasActiveCommand = True

        else:
            self.ActiveCommand.Update(DeltaSeconds)


    def ReceiveMessage(self, InDataMessage):

        if InDataMessage.DataType == "CB" and InDataMessage.Data["Head"] == "Request_CommandList":
            self.InitCommandList(InDataMessage.Data["Data"])

        elif InDataMessage.DataType == "EVN":
            if self.HasActiveCommand:
                self.ActiveCommand.OnProcessorReceivedEventNotification(InDataMessage)

        elif InDataMessage.DataType == "IN":

            if InDataMessage.Data["Head"] == "COMMAND_ProcessMessageCommands":
                self.ScanAndExecuteMessageCommands(InDataMessage.Data["Data"]["Message"], InDataMessage.Data["Data"]["WasFiltered"])


    def InitCommandList(self, InCommandList):

        for com in InCommandList:
            self.Commands[InCommandList[com]["Name"]] = AssignCommand(InCommandList[com]["Name"], InCommandList[com]["Calls"], InCommandList[com]["Atr"])

        for c in self.Commands:
            self.Commands[c].AssignProcessor(self)

        # Processing Commands
        for com in self.Commands:
            for call in self.Commands[com].Calls:
                self.CommandCalls[call] = self.Commands[com].Name
                self.CallLengths.add(len(call))


    def OnCurrentCommandFinished(self):
        self.HasActiveCommand = False
        self.LLogger.LogStatus("COMMAND: Finished Command Execution", False)


    def ScanAndExecuteMessageCommands(self, InChatMessage, InWasFiltered):
        Commands, CleanMessage = self.ScanMessageForCommands(InChatMessage.Message)
        self.LLogger.LogStatus(f"COMMAND: {Commands}", False)
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



def AssignCommand(InName, InCalls, InAtr):

    if "sfx" in InAtr:
        return Command_PlaySound(InName, InCalls, InAtr)

    elif InName == "VOICE":
        return Command_TTS(InName, InCalls, InAtr)


class Command_TTS(Command):
    def ExecuteCommand(self, InChatMessage):
        if len(InChatMessage.Message) > 0:
            #self.Processor.TTS.ConvertTTS(InChatMessage.Message)
            self.Processor.TransmitInstruction("TTS_ConvertTTS", InChatMessage.Message)
            self.Processor.TransmitInstruction("TTS_PlayTTS", {"UID" : "CommandTTS"})

            self.FinishOnTimer = False

            # GLady Avatar
            # if self.Processor.LObsInterface.Enabled:
            #     self.Processor.LObsInterface.SetFilterEnabled("GLadyAvatar", "Silent", False)
            self.Processor.TransmitInstruction("OBS_SetFilterEnabled", {"Source" : "GLadyAvatar", "Filter" : "Silent", "NewEnabled" : False})

    def FinishExecution(self):

        # if self.Processor.LObsInterface.Enabled:
        #     self.Processor.LObsInterface.SetFilterEnabled("GLadyAvatar", "Silent", True)
        self.Processor.TransmitInstruction("OBS_SetFilterEnabled", {"Source": "GLadyAvatar", "Filter": "Silent", "NewEnabled": True})
        super().FinishExecution()

    def OnProcessorReceivedEventNotification(self, InDataMessage):
        if InDataMessage.Data["Head"] == "TTS_FinishedPlayingTTS" and InDataMessage.Data["Data"]["UID"] == "CommandTTS":
            self.FinishExecution()


class Command_PlaySound(Command):
    def ExecuteCommand(self, InChatMessage):
        self.FinishOnTimer = False
        self.GifName = ""

        self.Processor.LLogger.LogStatus("Executing play sound")

        Volume = 1.0
        if "volume" in self.Atr:
            Volume = self.Atr["volume"]

        if "file" in self.Atr:
            #self.Timer = self.Processor.TTS.PlaySound("SFX/" + self.Atr["file"], self.Processor.LConfigController.Options["SFX_Volume"] * Volume)
            self.Processor.TransmitInstruction("TTS_PlaySFX", {"File" : "SFX/" + self.Atr["file"], "Volume" : Volume, "UID" : "CommandSFX"})

        else:
            #self.Timer = self.Processor.TTS.PlaySound("SFX/" + self.Name + ".mp3", self.Processor.LConfigController.Options["SFX_Volume"] * Volume)
            self.Processor.TransmitInstruction("TTS_PlaySFX", {"File": "SFX/" + self.Name + ".mp3", "Volume": Volume, "UID" : "CommandSFX"})

        if "time" in self.Atr:
            self.Timer = self.Atr["time"]

        if "time_inc" in self.Atr:
            self.Timer += self.Atr["time_inc"]

        if "obs_gif" in self.Atr:
            self.GifName = self.Name

            if "obs_gif_name" in self.Atr:
                self.GifName = self.Atr["obs_gif_name"]

            #self.Processor.LObsInterface.SetItemEnabledByName("GIFscene", self.GifName, True)
            self.Processor.TransmitInstruction("OBS_SetItemEnabled", {"Scene" : "GIFscene", "Item" : self.GifName, "NewEnabled" : True})


    def FinishExecution(self):

        if self.GifName != "":
            #self.Processor.LObsInterface.SetItemEnabledByName("GIFscene", self.GifName, False)
            self.Processor.TransmitInstruction("OBS_SetItemEnabled", {"Scene": "GIFscene", "Item": self.GifName, "NewEnabled": False})

        super().FinishExecution()


    def OnProcessorReceivedEventNotification(self, InDataMessage):
        if InDataMessage.Data["Head"] == "TTS_FinishedPlayingSFX" and InDataMessage.Data["Data"]["UID"] == "CommandSFX":
            self.FinishExecution()