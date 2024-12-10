from Source_Core import PluginImpl

class StreamEvents(PluginImpl.PluginBase):

    def __init__(self, InPluginManager):
        super().__init__(InPluginManager, "Init PLUGIN: Stream Events")

        self.Address = "StreamEvents"
        self.ConfigSection = "Events"
        self.Subscriptions = []
        self.Instructions = []

    def InitPlugin(self):
        super().InitPlugin()

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):
        pass

    def ReceiveMessage(self, InDataMessage):
        super().ReceiveMessage(InDataMessage)

    def ReadConfigData(self, InConfigFileLines):
        self.ReadOptions(InConfigFileLines)

    def InitPluginConfig(self):
        return self.InitOptionsConfig()