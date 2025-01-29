from Source_Core import PluginImpl

class UtilityInstructions(PluginImpl.PluginBase):

    def __init__(self, InPluginManager):
        super().__init__(InPluginManager, "Init PLUGIN: Utility Instructions")

        #self.Address = ...
        self.ConfigSection = ""
        self.Subscriptions = []
        self.Instructions = \
        [
            ("UFLOW_RunSection_Delayed", { "RequestAllRuntimeParameters" : True }),
            ("UFLOW_RunSection_Repeated", {"RequestAllRuntimeParameters": True}),

            # ("UFLOW_RunSection_IF_Greater", {"RequestAllRuntimeParameters": True}),
            # ("UFLOW_RunSection_IF_GreaterOrEqual", {"RequestAllRuntimeParameters": True}),
            # ("UFLOW_RunSection_IF_Less", {"RequestAllRuntimeParameters": True}),
            # ("UFLOW_RunSection_IF_LessOrEqual", {"RequestAllRuntimeParameters": True})
        ]

        self.SectionDelayTimers = []


    def InitPlugin(self):
        super().InitPlugin()

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):

        Finished = []
        for Delayed in self.SectionDelayTimers:

            Delayed["Time"] -= DeltaSeconds
            if Delayed["Time"] <= 0:

                Finished.append(Delayed)
                self.TransmitInstruction("INSTRUCTIONS_InterpretInstructions", {"Instructions" : Delayed["Code"][Delayed["Section"]]["Instructions"], "RuntimeParameters" : Delayed["RuntimeParameters"]})

        for F in Finished:
            self.SectionDelayTimers.remove(F)


    def ReceiveMessage(self, InDataMessage):
        super().ReceiveMessage(InDataMessage)

        if InDataMessage.DataType == "IN":

            if InDataMessage.Data["Head"] == "UFLOW_RunSection_Delayed":
                Data = InDataMessage.Data["Data"]
                self.RunSectionWithDelay(Data["Section"], Data["DelayTime"], Data["RuntimeParameters"])

            if InDataMessage.Data["Head"] == "UFLOW_RunSection_Repeated":
                Data = InDataMessage.Data["Data"]
                self.RunSectionWithDelay(Data["Section"], Data["RepeatTimes"], Data["RuntimeParameters"])


    def ReadConfigData(self, InConfigFileLines):
        self.ReadOptions(InConfigFileLines)

    def InitPluginConfig(self):
        return self.InitOptionsConfig()


    def RunSectionWithDelay(self, InSectionName, InDelayTime, InRuntimeParameters):

        if not "Code" in InRuntimeParameters:
            self.LLogger.LogError(
                f"UTILITY INSTRUCTIONS: 'UFLOW_RunSection_Delayed' failed to execute: no Code in runtime parameters!")
            return

        if not InSectionName in InRuntimeParameters["Code"]:
            self.LLogger.LogError(
                f"UTILITY INSTRUCTIONS: 'UFLOW_RunSection_Delayed' failed to execute: invalid code section: {InSectionName}!")
            return

        self.SectionDelayTimers.append( { "Time" : InDelayTime, "Code" : InRuntimeParameters["Code"], "Section" : InSectionName, "RuntimeParameters" :  InRuntimeParameters} )


    def RunSectionRepeated(self, InSectionName, InRepeatTimes, InRuntimeParameters):

        if not "Code" in InRuntimeParameters:
            self.LLogger.LogError(
                f"UTILITY INSTRUCTIONS: 'UFLOW_RunSection_Delayed' failed to execute: no Code in runtime parameters!")
            return

        if not InSectionName in InRuntimeParameters["Code"]:
            self.LLogger.LogError(
                f"UTILITY INSTRUCTIONS: 'UFLOW_RunSection_Delayed' failed to execute: invalid code section: {InSectionName}!")
            return

        for i in range(InRepeatTimes):
            self.TransmitInstruction("INSTRUCTIONS_InterpretInstructions", {"Instructions" : InRuntimeParameters["Code"][InSectionName], "RuntimeParameters" : InRuntimeParameters})

