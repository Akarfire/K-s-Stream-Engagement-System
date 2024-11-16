import sys
import os
import importlib.util
from pathlib import Path
import random

from Source_Core.AddressManagement import AddressManager
from Source_Core.CommunicationBus import CoreComponent_BusConnected

class PluginBase:

    PluginList = []

    def __init__(self):
        self.MyCore = None
        self.Address = "Plugin" + str(random.randint(10000, 99999))

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.PluginList.append(cls)

    def InitPlugin(self, InPluginManager):
        self.MyPluginManager = InPluginManager

    def TransmitRequest(self, DataMessage):
        self.MyPluginManager.ReceivedData(DataMessage)

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):
        pass

    def ReceiveRequest(self, DataMessage):
        pass


class PluginManager(CoreComponent_BusConnected):

    def __init__(self, InCore, InAddress):
        super().__init__(InCore, InAddress)

        self.Plugins = []

        self.PluginAddressManager = AddressManager(self.MyCore.MyLogger)
        self.LLogger = self.MyCore.MyLogger


    def LoadPluginModule(self, Path):

        Name = os.path.split(Path)[-1].replace(".py", '')
        Spec = importlib.util.spec_from_file_location(Name, Path)
        Module = importlib.util.module_from_spec(Spec)
        sys.modules[Name] = Module
        Spec.loader.exec_module(Module)

        return Module


    def LoadPlugins(self):

        Path("Plugins").mkdir(parents=True, exist_ok=True)

        for File in os.listdir("Plugins"):
            if File.endswith(".py"):
                try:
                    self.LoadPluginModule(os.getcwd() + "/Plugins/" + File)
                    self.LLogger.LogStatus(f"PLUGIN {File} loaded")

                except Exception as e:
                    self.LLogger.LogError(f"PLUGIN {File} failed to load: {e}")


    def InitPlugins(self):

        for p in PluginBase.PluginList:
            Inst = p()
            Inst.InitPlugin(self)
            self.Plugins.append(Inst)

            Address = "PLUGIN_" + Inst.Address
            self.PluginAddressManager.RegisterAddress(Address, Inst)
            self.MyCommunicationBus.RegisterAdress(Address, self)


    def ReceivedData(self, InDataMessage):

        # If the receiver is a plugin
        if self.PluginAddressManager.IsValidAddress(InDataMessage.ReceiverAddress):
            self.PluginAddressManager.GetComponent(InDataMessage.ReceiverAddress).ReceiveRequest(InDataMessage)

        # If sender is a plugin and it is sending a request to the core
        elif self.PluginAddressManager.IsValidAddress(InDataMessage.SenderAddress):
            self.TransmitData(InDataMessage)

