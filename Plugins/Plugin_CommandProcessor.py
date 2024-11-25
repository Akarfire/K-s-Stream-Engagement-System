from Source_Core import PluginImpl
import queue
from Source_Core.Types import InstructionCodeHeader


class Command:
    def __init__(self, InName, InCalls, InAtr):
        self.Name = InName
        self.Calls = InCalls
        self.Atr = InAtr
        self.Instructions = dict()
        self.Processor = None

        self.FinishOnTimer = True
        self.Timer = 0
        if "time" in self.Atr:
            self.Timer = self.Atr["time"]

    def AssignProcessor(self, InProcessor):
        self.Processor = InProcessor

    def AssignInstructions(self, InInstructions):
        print(InInstructions)
        self.Instructions = InInstructions

        for Section in self.Instructions:
            if self.Instructions[Section]["Header"].Type == "EVENT":
                self.Processor.RegisterEventSubscription(self.Instructions[Section]["Header"].Name)

    def Update(self, DeltaTime):
        if self.FinishOnTimer:
            self.Timer -= DeltaTime
            if self.Timer <= 0:
                self.FinishExecution()

    def ExecuteCommand(self, InChatMessage):
        if "BLOCK_Start" in self.Instructions:
            self.Processor.TransmitInstruction("INSTRUCTIONS_InterpretInstructions", {"Instructions" : self.Instructions["BLOCK_Start"]["Instructions"]})

        if "BLOCK_Default" in self.Instructions:
            self.Processor.TransmitInstruction("INSTRUCTIONS_InterpretInstructions", {"Instructions" : self.Instructions["BLOCK_Default"]["Instructions"]})

    def FinishExecution(self):
        pass

    def OnProcessorReceivedEventNotification(self, InDataMessage):
        if "EVENT_" + InDataMessage.Data["Head"] in self.Instructions:
            self.Processor.TransmitInstruction("INSTRUCTIONS_InterpretInstructions", {"Instructions" : self.Instructions["EVENT_" + InDataMessage.Data["Head"]]["Instructions"]})


class QueuedCommand:
    def __init__(self, InCommand, InChatMessage):
        self.Command = InCommand
        self.Message = InChatMessage



class CommandProcessor(PluginImpl.PluginBase):

    def __init__(self, InPluginManager):
        super().__init__(InPluginManager)

        self.Address = "CommandProcessor"
        self.ConfigSection = "Commands"
        self.Subscriptions = []
        self.Instructions = ["COMMAND_ProcessMessageCommands", "COMMAND_Finish"]

        self.LLogger = None

        self.Commands = dict()
        self.CommandCalls = {}
        self.CallLengths = set()

        self.InstructionParsingWaiters = queue.Queue()

        # Queue
        self.CommandQueue = queue.Queue()
        self.HasActiveCommand = False
        self.ActiveCommand = None


    def InitPlugin(self):
        super().InitPlugin()

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

        super().ReceiveMessage(InDataMessage)

        if InDataMessage.DataType == "EVN":
            if self.HasActiveCommand:
                self.ActiveCommand.OnProcessorReceivedEventNotification(InDataMessage)

        elif InDataMessage.DataType == "IN":

            if InDataMessage.Data["Head"] == "COMMAND_ProcessMessageCommands":
                self.ScanAndExecuteMessageCommands(InDataMessage.Data["Data"]["Message"],
                                                   InDataMessage.Data["Data"]["WasFiltered"])

            elif InDataMessage.Data["Head"] == "COMMAND_Finish":
                self.ActiveCommand.FinishExecution()
                self.OnCurrentCommandFinished()

        elif InDataMessage.DataType == "CB":

            if InDataMessage.Data["Head"] == "INSTRUCTIONS_ParseInstructionCode":
                Command = self.InstructionParsingWaiters.get()
                Command.AssignInstructions(InDataMessage.Data["Data"]["Instructions"])


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


    def ReadConfigData(self, InConfigFileLines):

        i = 0
        CurrentCommandLines = []
        while i < len(InConfigFileLines):
            if InConfigFileLines[i] != '':

                if InConfigFileLines[i].replace(' ', '') == '-':
                    self.ProcessCommandLines(CurrentCommandLines)
                    CurrentCommandLines = []

                else:
                    CurrentCommandLines.append(InConfigFileLines[i])

            i += 1

        if len(CurrentCommandLines) > 0:
            self.ProcessCommandLines(CurrentCommandLines)


    def ProcessCommandLines(self, CommandLines):

        Name = ""
        Calls = set()
        Atr = {}
        Error = False

        CollectingInstructions = False
        CollectedInstructionLines = []

        for line in CommandLines:
            if line.count(':') == 1:
                Param, Values = line.replace(' ', '').split(':')

                if Param == "name":
                    # If name is already set
                    if Name != '':
                        self.LLogger.LogError("COMMAND PROCESSOR: Tried to declare a command with multiple names: " + line)
                        Error = True
                        break

                    Name = Values
                    Calls.add(Name)

                elif Param == "calls":
                    for call in Values.split(','):
                        Calls.add(call.upper())

                elif Param == "atr":
                    for atr in Values.split(','):
                        if '=' in atr:

                            atr_name, atr_value_data = atr.split('=')

                            # Processing attribute types
                            if "[b]" in atr_value_data:
                                Atr[atr_name] = atr_value_data.replace('[b]', '').lower() == "true"

                            elif "[i]" in atr_value_data:
                                Atr[atr_name] = int(atr_value_data.replace('[i]', ''))

                            elif "[f]" in atr_value_data:
                                Atr[atr_name] = float(atr_value_data.replace('[f]', ''))

                            if "[s]" in atr_value_data:
                                Atr[atr_name] = atr_value_data.replace('[s]', '')

                        else:
                            Atr[atr] = True

                elif Param == "instr":
                    CollectingInstructions = True
                    CollectedInstructionLines.append(Values)

            elif CollectingInstructions:

                if line.endswith('/'):
                    CollectedInstructionLines.append(line.replace('/', ''))
                    CollectingInstructions = False

                else:
                    CollectedInstructionLines.append(line)

        if not Error:
            self.Commands[Name] = Command(Name, Calls, Atr)
            self.Commands[Name].AssignProcessor(self)

            for call in Calls:
                self.CommandCalls[call] = self.Commands[Name].Name
                self.CallLengths.add(len(call))

            if len(CollectedInstructionLines) > 0:
                self.InstructionParsingWaiters.put(self.Commands[Name])
                self.TransmitMessage("Instructions", "RE", {"Head" : "INSTRUCTIONS_ParseInstructionCode", "Data" : {"Code" : CollectedInstructionLines}})


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