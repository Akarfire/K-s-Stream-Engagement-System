from Source_Core import PluginImpl

class SamplePlugin(PluginImpl.PluginBase):

    def __init__(self):
        super().__init__()

        #self.Address = ...
        self.ConfigSection = ""
        self.Subscriptions = []
        self.Instructions = []

    def InitPlugin(self, InPluginManager):
        super().InitPlugin(InPluginManager)

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):
        pass

    def ReceiveMessage(self, InDataMessage):
        super().ReceiveMessage(InDataMessage)

    def ReadConfigData(self, InConfigFileLines):
        self.ReadOptions(InConfigFileLines)

