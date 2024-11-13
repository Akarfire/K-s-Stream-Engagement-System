from Source_Core import PluginImpl

class SamplePlugin(PluginImpl.PluginBase):

    def __init__(self):
        super().__init__()
        pass

    def InitPlugin(self, InCore):
        super().InitPlugin(InCore)

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):
        pass

    def SendDataToPlugin(self, Data):
        pass

    def SendDataToServer(self, Data):
        pass