from Source_Core import PluginImpl

class SamplePlugin(PluginImpl.PluginBase):

    def __init__(self, InPluginManager):
        super().__init__(InPluginManager)

        #self.Address = ...
        self.ConfigSection = ""
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

