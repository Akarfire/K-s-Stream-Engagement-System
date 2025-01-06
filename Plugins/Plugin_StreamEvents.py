from Source_Core import PluginImpl
import random

# Contains parameters of an event, that describe its behavior
class EventConfiguration:

    def __init__(self):

        self.Duration = 1.0
        self.MaxAtSameMoment = 1
        self.UpdateFrequency = 1

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
        self.Timer = self.Configuration.Duration


    def ExecuteInstrucntions(self, InCodeBlock):

        if InCodeBlock in self.Configuration.Instructions:
            self.EventProcessor.TransmitInstruction("INSTRUCTIONS_InterpretInstructions", {"Instructions": self.Configuration.Instructions[InCodeBlock]["Instructions"], "RuntimeParameters": self.CachedParameters})


    def StartEvent(self, InParameters = None):

        self.Active = True

        if InParameters != None:
            self.CachedParameters = InParameters.copy()
        self.CachedParameters["Code"] = self.Configuration.Instructions

        self.ExecuteInstrucntions("Start")


    def UpdatedEvent(self, InDeltaTime):

        if self.Active:

            self.ExecuteInstrucntions("Update")

            self.Timer -= InDeltaTime
            if self.Timer <= 0:
                self.FinishEvent()


    def SetPaused(self, InNewPaused):
        self.Active = not InNewPaused


    def FinishEvent(self):

        self.Active = False

        self.ExecuteInstrucntions("End")

        self.EventProcessor.OnEventFinished(self.Name, self.UniqueName)


# Actual Plugin
class StreamEvents(PluginImpl.PluginBase):

    def __init__(self, InPluginManager):
        super().__init__(InPluginManager, "Init PLUGIN: Stream Events")

        self.Address = "StreamEvents"
        self.ConfigSection = "Events"
        self.Subscriptions = []
        self.Instructions = []

        # < Unique Name - Event Configuration >
        self.EventsLib = dict()

        # < General Name - Queue < InParameters > >
        self.EventQueue = dict()

        # < General Name - dict < Unique Name - Event > >
        self.ActiveEvents = dict()


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
                self.ActiveEvents[GeneralEvent][UniqueEvent].UpdateEvent(DeltaSeconds)


    def ReceiveMessage(self, InDataMessage):
        super().ReceiveMessage(InDataMessage)

    def ReadConfigData(self, InConfigFileLines):
        self.ReadOptions(InConfigFileLines)

    def InitPluginConfig(self):
        return self.InitOptionsConfig()


    def CallEvent(self, InGeneralEventName, InParameters):

        if not InGeneralEventName in self.EventsLib:
            self.LLogger.LogError(f"STREAM EVENTS: Event '{InGeneralEventName}' does not exist!")

        self.EventQueue[InGeneralEventName].put(InParameters)


    def StartEvent(self, InGeneralEventName, InParameters):

        UniqueName = InGeneralEventName + '_' + str(len(self.ActiveEvents[InGeneralEventName])) + '_' + str(random.randint(10000, 99999))
        NewEvent = Event(self, InGeneralEventName, UniqueName, self.EventsLib[InGeneralEventName])
        self.ActiveEvents[InGeneralEventName][UniqueName] = NewEvent

        NewEvent.StartEvent(InParameters)


    def OnEventFinished(self, InGeneralName, InUniqueEventName):
        self.ActiveEvents[InGeneralName].Pop(InUniqueEventName)

