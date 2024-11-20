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

    def __init__(self, InPluginManager):

        self.MyPluginManager = InPluginManager
        self.LLogger = self.MyPluginManager.LLogger
        self.MyCore = InPluginManager.MyCore
        self.Address = "Plugin" + str(random.randint(10000, 99999))
        self.ConfigSection = ""
        self.Config = {"Options" : {}}

        self.Subscriptions = []
        self.Instructions = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.PluginList.append(cls)

    def InitPlugin(self): # OVERRIDE
        pass

    def TransmitMessage(self, InReceiverAddress, InType, InData):
        RequestDataMessage = DataMessage(InReceiverAddress, self.Address, InType, InData)
        self.MyPluginManager.ReceivedData(RequestDataMessage)

    def TransmitEvent(self, InEventName, InData):
        EventDataMessage = DataMessage("-", self.Address, "EV", {"Head" : InEventName, "Data" : InData})
        self.MyPluginManager.ReceivedData(EventDataMessage)

    def TransmitInstruction(self, InInstructionName, InArguments):
        InstructionMessage = DataMessage("Instructions", self.Address, "IN", {"Head" : InInstructionName, "Data" : InArguments})
        self.MyPluginManager.ReceivedData(InstructionMessage)

    def DeletePlugin(self): # OVERRIDE
        pass

    def UpdatePlugin(self, DeltaSeconds): # OVERRIDE
        pass

    def ReceiveMessage(self, InDataMessage): # OVERRIDE
        if InDataMessage.DataType == "CB" and InDataMessage.Data["Head"] == "PluginConfigRequest":
            self.ReadConfigData(InDataMessage.Data["Data"]["ConfigLines"])

        elif InDataMessage.DataType == "RE" and InDataMessage.Data["Head"] == "PluginInitConfigRequest":
            self.TransmitMessage(InDataMessage.SenderAddress, "CB", {"Head" : "PluginInitConfigRequest", "Data" : {"ConfigSectionName" : self.ConfigSection, "ConfigLines" : self.InitPluginConfig()}})
        # Override

    def RequestConfigData(self):
        self.TransmitMessage("Config", "RE", {"Head" : "PluginConfigRequest", "Data" : {"ConfigSection" : self.ConfigSection}})

    def ReadConfigData(self, InConfigFileLines): # OVERRIDE
        self.ReadOptions(InConfigFileLines)

    def ReadOptions(self, InOptionLines):

        i = 0
        while i < len(InOptionLines):

            OptionLine = InOptionLines[i]

            if len(OptionLine) > 0 and OptionLine.count('=') == 1:

                Name, Value = OptionLine.replace(' ', '').split('=')

                if '[b]' in Value:
                    self.Config["Options"][Name] = Value.replace('[b]', '').lower() == "true"

                elif '[i]' in Value:
                    self.Config["Options"][Name] = int(Value.replace('[i]', ''))

                elif '[f]' in Value:
                    self.Config["Options"][Name] = float(Value.replace('[f]', ''))

                elif '[s]' in Value:
                    self.Config["Options"][Name] = Value.replace('[s]', '')

                else:
                    self.Config["Options"][Name] = Value

            i += 1

    def InitPluginConfig(self):
        return self.InitOptionsConfig()


    def InitOptionsConfig(self):
        OptionLines = []
        for i in self.Config["Options"]:
            OptionLines.append(i + " = " + '[' + type(self.Config["Options"][i]).__name__[0] + ']' + str(self.Config["Options"][i]).lower() + "\n")

        return OptionLines


    def AddOption(self, InOptionName, InDefaultValue):

        if not "Options" in self.Config:
            self.Config["Options"] = dict()

        self.Config["Options"][InOptionName] = InDefaultValue


    def GetOption(self, InOptionName):

        if "Options" in self.Config:
            if InOptionName in self.Config["Options"]:
                return self.Config["Options"][InOptionName]

        self.LLogger.LogError(f"{self.Address.upper()}: Has no options named {InOptionName}")
        return None


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
            Inst = p(self)

            Address = "PLUGIN_" + Inst.Address
            Inst.Address = Address
            self.PluginAddressManager.RegisterAddress(Address, Inst)
            self.MyCommunicationBus.RegisterAddress(Address, self)

            Inst.RequestConfigData()
            Inst.InitPlugin()
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

