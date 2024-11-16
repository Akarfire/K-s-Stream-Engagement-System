from Source_Core import PluginImpl

class SamplePlugin(PluginImpl.PluginBase):

    def __init__(self):
        super().__init__()
        pass

    def InitPlugin(self, InPluginManager):
        super().InitPlugin(InPluginManager)

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):
        pass

    def ReceiveRequest(self, DataMessage):
        pass

