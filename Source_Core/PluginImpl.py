import sys
import os
import importlib.util
from pathlib import Path
import random

from Source_Core.AddressManagement import AddressManager
from Source_Core.CommunicationBus import CoreComponent_BusConnected
from Source_Core.Types import DataMessage


class PluginBase:

    PluginList = []

    def __init__(self):
        self.MyCore = None
        self.Address = "Plugin" + str(random.randint(10000, 99999))

        self.Subscriptions = []
        self.Instructions = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.PluginList.append(cls)

    def InitPlugin(self, InPluginManager):
        self.MyPluginManager = InPluginManager
        self.MyCore = InPluginManager.MyCore

    def TransmitMessage(self, InReceiverAddress, InType, InData):
        RequestDataMessage = DataMessage(InReceiverAddress, self.Address, InType, InData)
        self.MyPluginManager.ReceivedData(RequestDataMessage)

    def TransmitEvent(self, InEventName, InData):
        EventDataMessage = DataMessage("-", self.Address, "EV", {"Head" : InEventName, "Data" : InData})
        self.MyPluginManager.ReceivedData(EventDataMessage)

    def TransmitInstruction(self, InInstructionName, InArguments):
        InstructionMessage = DataMessage("Instructions", self.Address, "IN", {"Head" : InInstructionName, "Data" : InArguments})
        self.MyPluginManager.ReceivedData(InstructionMessage)

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):
        pass

    def ReceiveMessage(self, InDataMessage):
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

            Address = "PLUGIN_" + Inst.Address
            Inst.Address = Address
            self.PluginAddressManager.RegisterAddress(Address, Inst)
            self.MyCommunicationBus.RegisterAddress(Address, self)

            Inst.InitPlugin(self)
            self.Plugins.append(Inst)

            for Sub in Inst.Subscriptions:
                self.PluginAddressManager.RegisterSubscription(Sub, Inst.Address)
                self.MyCommunicationBus.RegisterSubscription(Sub, Inst.Address)

            for Instruction in Inst.Instructions:
                self.MyCore.MyInstructionProcessor.RegisterInstruction(Instruction, Inst.Address)



    def UpdatePlugins(self, InDeltaTime):

        for Plugin in self.Plugins:
            Plugin.UpdatePlugin(InDeltaTime)


    def ReceivedData(self, InDataMessage):
        if InDataMessage.DataType in ["RE", "CB", "EVN", "IN"]:

            # If the receiver is a plugin
            if self.PluginAddressManager.IsValidAddress(InDataMessage.ReceiverAddress):
                self.PluginAddressManager.GetComponent(InDataMessage.ReceiverAddress).ReceiveMessage(InDataMessage)

            # If sender is a plugin, and it is sending a request to the core
            elif self.PluginAddressManager.IsValidAddress(InDataMessage.SenderAddress):
                self.TransmitData(InDataMessage)


        elif InDataMessage.DataType == "EV":
            self.TransmitData(InDataMessage)

