from Source_Core import PluginImpl

class SamplePlugin(PluginImpl.PluginBase):

    def __init__(self):
        super().__init__()

    def InitPlugin(self, InPluginManager):
        super().InitPlugin(InPluginManager)
        self.Subscriptions = []
        self.Instructions = []

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):
        pass

    def ReceiveMessage(self, InDataMessage):
        pass

