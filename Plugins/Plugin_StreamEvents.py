import queue

from Source_Core import PluginImpl
import random

from Source_Core.InstructionProcessor import RuntimeParameter


# Contains parameters of an event, that describe its behavior
class EventConfiguration:

    def __init__(self):

        self.Duration = 1.0
        self.MaxAtSameMoment = 1
        self.UpdateFrequency = 10

        self.Instructions = dict()


# Event Class, used in the plugin
class Event:

    def __init__(self, InEventProcessor, InEventName, InUniqueName, InEventConfiguration):

        self.EventProcessor = InEventProcessor

        self.Name = InEventName
        self.UniqueName = InUniqueName
        self.Configuration = InEventConfiguration

        self.CachedParameters = dict()
        self.Active = False


    def ExecuteInstructions(self, InCodeBlock):

        if InCodeBlock in self.Configuration.Instructions:

            RuntimeParameters = dict()
            for Parameter in self.CachedParameters:
                RuntimeParameters[ "EVENT_" + Parameter ] = self.CachedParameters[Parameter]

            self.EventProcessor.TransmitInstruction("INSTRUCTIONS_InterpretInstructions", {"Instructions": self.Configuration.Instructions[InCodeBlock]["Instructions"], "RuntimeParameters": RuntimeParameters})


    def StartEvent(self, InParameters = None):

        self.Timer = self.Configuration.Duration
        self.Active = True

        if InParameters != None:
            self.CachedParameters = InParameters.copy()
        self.CachedParameters["Code"] = self.Configuration.Instructions

        self.ExecuteInstructions("BLOCK_Start")


    def UpdateEvent(self, InDeltaTime):

        if self.Active:

            self.ExecuteInstructions("BLOCK_Update")

            self.Timer -= InDeltaTime
            if self.Timer <= 0:
                self.FinishEvent()


    def SetPaused(self, InNewPaused):
        self.Active = not InNewPaused


    def FinishEvent(self):

        self.Active = False

        self.ExecuteInstructions("BLOCK_End")

        self.EventProcessor.OnEventFinished(self.Name, self.UniqueName)


class MidParsingEventData():

    def __init__(self):

        self.Name = ""
        self.Attributes = dict()
        self.Instructions = dict()


# Actual Plugin
class StreamEvents(PluginImpl.PluginBase):

    def __init__(self, InPluginManager):
        super().__init__(InPluginManager, "Init PLUGIN: Stream Events")

        self.Address = "StreamEvents"
        self.ConfigSection = "Events"
        self.Subscriptions = []
        self.Instructions = [("EVENTS_CallEvent", {}), ("EVENTS_PauseEvent", {})]

        # < Unique Name - Event Configuration >
        self.EventsLib = dict()

        # < General Name - Queue < InParameters > >
        self.EventQueue = dict()

        # < General Name - dict < Unique Name - Event > >
        self.ActiveEvents = dict()

        # < Unique Name - Time since last update >
        self.ActiveEventsDeltaTimer = dict()

        # < MidParsingEventData >
        self.ParsingQueue = queue.Queue()

        # Events that have finished during this update < General Name - [ UniqueNames ] >
        self.FinishedEvents = dict()


    def InitPlugin(self):
        super().InitPlugin()

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):

        # Start queued events
        for GeneralEvent in self.EventQueue:
            if not self.EventQueue[GeneralEvent].empty():
                if (self.EventsLib[GeneralEvent].MaxAtSameMoment == 0) or (self.EventsLib[GeneralEvent].MaxAtSameMoment > len(self.ActiveEvents[GeneralEvent])):
                    self.StartEvent(GeneralEvent, self.EventQueue[GeneralEvent].get())

        # Update active events
        for GeneralEvent in self.ActiveEvents:
            for UniqueEvent in self.ActiveEvents[GeneralEvent]:

                # Handling update frequency
                self.ActiveEventsDeltaTimer[UniqueEvent] += DeltaSeconds
                if self.ActiveEventsDeltaTimer[UniqueEvent] > ( 1 / self.EventsLib[GeneralEvent].UpdateFrequency):
                    self.ActiveEvents[GeneralEvent][UniqueEvent].UpdateEvent(DeltaSeconds)

        # Process finished events
        for GEvent in self.FinishedEvents:
            for UEvent in self.FinishedEvents[GEvent]:
                self.ActiveEvents[GEvent].pop(UEvent)
                self.LLogger.LogStatus(f"STREAM EVENTS: Finished Event '{GEvent}'", False)

            self.FinishedEvents[GEvent].clear()


    def ReceiveMessage(self, InDataMessage):
        super().ReceiveMessage(InDataMessage)

        if InDataMessage.DataType == "IN":

            # Calling Events
            if InDataMessage.Data["Head"] == "EVENTS_CallEvent":
                self.CallEvent(InDataMessage.Data["Data"]["EventName"], InDataMessage.Data["Data"])

            # Pause events
            if InDataMessage.Data["Head"] == "EVENTS_PauseEvent":
                if InDataMessage.Data["Data"]["EventName"] in self.ActiveEvents:

                    if "UniqueName" in InDataMessage.Data["Data"]:
                        if InDataMessage.Data["Data"]["UniqueName"] in self.ActiveEvents[InDataMessage.Data["Data"]["EventName"]]:
                            self.ActiveEvents[InDataMessage.Data["Data"]["EventName"]][InDataMessage.Data["Data"]["UniqueName"]].PauseEvent()

                    else:
                        for UEvent in self.ActiveEvents[InDataMessage.Data["Data"]["EventName"]]:
                            self.ActiveEvents[InDataMessage.Data["Data"]["EventName"]][UEvent].PauseEvent()


        elif InDataMessage.DataType == "CB":

            if InDataMessage.Data["Head"] == "INSTRUCTIONS_ParseInstructionCode":
                EventData = self.ParsingQueue.get()
                EventData.Instructions = InDataMessage.Data["Data"]["Instructions"]
                self.WriteEvent(EventData)


    def ReadConfigData(self, InConfigFileLines):

        i = 0
        CurrentLines = []
        while i < len(InConfigFileLines):
            if InConfigFileLines[i] != '':

                if InConfigFileLines[i].replace(' ', '') == '-':
                    self.ProcessCommandLines(CurrentLines)
                    CurrentLines = []

                else:
                    CurrentLines.append(InConfigFileLines[i])

            i += 1

        if len(CurrentLines) > 0:
            self.ProcessCommandLines(CurrentLines)


    def ProcessCommandLines(self, EventLines):

        Name = ""
        Atr = {}
        Error = False

        CollectingInstructions = False
        CollectedInstructionLines = []

        for line in EventLines:

            if CollectingInstructions:

                if line.endswith('/'):
                    CollectedInstructionLines.append(line.replace('/', ''))
                    CollectingInstructions = False

                else:
                    CollectedInstructionLines.append(line)

            if line.count(':') == 1:
                Param, Values = line.replace(' ', '').split(':')

                if Param == "name":
                    # If name is already set
                    if Name != '':
                        self.LLogger.LogError(
                            "EVENTS: Tried to declare an event with multiple names: " + line)
                        Error = True
                        break

                    Name = Values

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

        if not Error:

            EventParsingData = MidParsingEventData()

            EventParsingData.Name = Name
            EventParsingData.Attributes = Atr.copy()

            if len(CollectedInstructionLines) > 0:
                self.ParsingQueue.put(EventParsingData)
                self.TransmitMessage("Instructions", "RE", {"Head": "INSTRUCTIONS_ParseInstructionCode",
                                                            "Data": {"Code": CollectedInstructionLines}})
            else:
                self.WriteEvent(EventParsingData)


    def InitPluginConfig(self):
        return self.InitOptionsConfig()


    def CallEvent(self, InGeneralEventName, InParameters):

        if not InGeneralEventName in self.EventsLib:
            self.LLogger.LogError(f"STREAM EVENTS: Event '{InGeneralEventName}' does not exist!")

        self.EventQueue[InGeneralEventName].put(InParameters)

        self.LLogger.LogStatus(f"STREAM EVENTS: Called Event '{InGeneralEventName}'", False)


    def WriteEvent(self, InEventParsingData):

        NewEventConfiguration = EventConfiguration()
        NewEventConfiguration.Instructions = InEventParsingData.Instructions

        if "Duration" in InEventParsingData.Attributes:
            NewEventConfiguration.Duration = InEventParsingData.Attributes["Duration"]

        if "MaxAtSameMoment" in InEventParsingData.Attributes:
            NewEventConfiguration.MaxAtSameMoment = InEventParsingData.Attributes["MaxAtSameMoment"]

        if "UpdateFrequency" in InEventParsingData.Attributes:
            NewEventConfiguration.UpdateFrequency = InEventParsingData.Attributes["UpdateFrequency"]

        self.EventsLib[InEventParsingData.Name] = NewEventConfiguration

        self.EventQueue[InEventParsingData.Name] = queue.Queue()
        self.ActiveEvents[InEventParsingData.Name] = dict()
        self.FinishedEvents[InEventParsingData.Name] = []


    def StartEvent(self, InGeneralEventName, InParameters):

        UniqueName = InGeneralEventName + '_' + str(len(self.ActiveEvents[InGeneralEventName])) + '_' + str(random.randint(10000, 99999))
        NewEvent = Event(self, InGeneralEventName, UniqueName, self.EventsLib[InGeneralEventName])
        self.ActiveEvents[InGeneralEventName][UniqueName] = NewEvent
        self.ActiveEventsDeltaTimer[UniqueName] = 0

        NewEvent.StartEvent(InParameters)

        self.LLogger.LogStatus(f"STREAM EVENTS: Started Event '{InGeneralEventName}'", False)


    def OnEventFinished(self, InGeneralName, InUniqueEventName):
        self.FinishedEvents[InGeneralName].append(InUniqueEventName)

