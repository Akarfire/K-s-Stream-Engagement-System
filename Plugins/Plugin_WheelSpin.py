import queue

from numba.core.cgutils import false_bit

from Source_Core import PluginImpl
import random


class Spin:

    def __init__(self, InWheelSpinManager, InName, InSpinsMin, InSpinsMax, InSpinSpeed, InResults):

        # Data
        self.WheelSpinManager = InWheelSpinManager
        self.Name = InName
        self.SpinsMin = InSpinsMin
        self.SpinsMax = InSpinsMax
        self.SpinSpeed = InSpinSpeed
        self.Results = InResults
        self.Instructions = dict()

        # Status
        self.Spinning = False
        self.LatestResult = 0
        self.CurrentPosition = 0
        self.CurrentSpin = 0
        self.CurrentMaxSpin = 0
        self.CurrentTimer = 0


    def AssignInstructions(self, InInstructions):
        self.Instructions = InInstructions

    def TransmitInstruction(self, InCodeBlock):

        RuntimeParameters = dict()
        RuntimeParameters["SPIN_Name"] = self.Name
        RuntimeParameters["SPIN_LatestResult"] = self.Results[self.LatestResult]
        RuntimeParameters["SPIN_CurrentPosition"] = self.Results[self.CurrentPosition]
        RuntimeParameters["SPIN_CurrentSpin"] = self.CurrentSpin
        RuntimeParameters["SPIN_CurrentMaxSpin"] = self.CurrentMaxSpin
        RuntimeParameters["SPIN_CurrentTimer"] = self.CurrentTimer

        self.WheelSpinManager.TransmitInstruction("INSTRUCTIONS_InterpretInstructions", {"Instructions": self.Instructions[InCodeBlock]["Instructions"], "RuntimeParameters": RuntimeParameters})


    def StartSpin(self):

        self.WheelSpinManager.LLogger.LogStatus(f"WHEEL SPIN: Started spin '{self.Name}'")

        self.CurrentMaxSpin = random.randint(self.SpinsMin, self.SpinsMax)
        self.CurrentSpin = 0
        self.CurrentTimer = 0.1 * self.SpinSpeed * 1 / self.CurrentMaxSpin

        self.TransmitInstruction("BLOCK_BeforeSpin")

        self.Spinning = True


    def Update(self, InDeltaTime):

        if self.Spinning:

            self.CurrentTimer -= InDeltaTime
            if self.CurrentTimer <= 0:
                self.CurrentPosition = (self.CurrentPosition + 1) % len(self.Results)
                self.CurrentTimer = 0.3 * self.SpinSpeed * (self.CurrentSpin / self.CurrentMaxSpin) ** 2
                self.CurrentSpin += 1

                self.TransmitInstruction("BLOCK_SpinUpdate")

                if self.CurrentSpin >= self.CurrentMaxSpin:
                    self.FinishSpin()


    def FinishSpin(self):

        self.WheelSpinManager.LLogger.LogStatus(f"WHEEL SPIN: Spin '{self.Name}' finished with result '{self.Results[self.CurrentPosition]}'")

        self.LatestResult = self.CurrentPosition
        self.Spinning = False

        self.TransmitInstruction("BLOCK_AfterSpin")




class WheelSpin(PluginImpl.PluginBase):

    def __init__(self, InPluginManager):
        super().__init__(InPluginManager, "Init PLUGIN: WheelSpin")

        self.Address = "WheelSpin"
        self.ConfigSection = "WheelSpin"
        self.Subscriptions = []
        self.Instructions = [ ("SPINS_SpinWheel", {}) ]

        # All possible spins < SpinName - Spin >
        self.Spins = dict()

        # Queue of awaiting Spins < SpinName >
        self.SpinQueue = queue.Queue()

        # Queue of spins, that are awaiting instruction parsing
        self.InstructionParsingQueue = queue.Queue()


    def InitPlugin(self):
        super().InitPlugin()

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):

        for spin in self.Spins:
            if self.Spins[spin].Spinning:
                self.Spins[spin].Update(DeltaSeconds)

        if not self.SpinQueue.empty():
            TopSpin = self.SpinQueue.get()

            if not self.Spins[TopSpin].Spinning:
                self.Spins[TopSpin].StartSpin()

            else:
                self.SpinQueue.put(TopSpin)


    def CallSpin(self, SpinName):

        if not SpinName in self.Spins:
            self.LLogger.LogError(f"WHEEL SPIN: Tried calling spin '{SpinName}', which does not exist!")
            return

        self.LLogger.LogStatus(f"WHEEL SPIN: Called spin '{SpinName}'")
        self.SpinQueue.put(SpinName)


    def ReceiveMessage(self, InDataMessage):
        super().ReceiveMessage(InDataMessage)

        if InDataMessage.DataType == "IN":

            if InDataMessage.Data["Head"] == "SPINS_SpinWheel":
                self.CallSpin(InDataMessage.Data["Data"]["SpinWheelName"])

        elif InDataMessage.DataType == "CB":

            if InDataMessage.Data["Head"] == "INSTRUCTIONS_ParseInstructionCode":
                SpinName = self.InstructionParsingQueue.get()
                self.Spins[SpinName].AssignInstructions(InDataMessage.Data["Data"]["Instructions"])


    def ReadConfigData(self, InConfigFileLines):

        i = 0
        CurrentLines = []
        while i < len(InConfigFileLines):
            if InConfigFileLines[i] != '':

                if InConfigFileLines[i].replace(' ', '') == '-':
                    self.ProcessSpinLines(CurrentLines)
                    CurrentLines = []

                else:
                    CurrentLines.append(InConfigFileLines[i])

            i += 1

        if len(CurrentLines) > 0:
            self.ProcessSpinLines(CurrentLines)


    def ProcessSpinLines(self, SpinLines):

        Name = ""
        Atr = {}
        Results = []
        Error = False

        CollectingInstructions = False
        CollectedInstructionLines = []

        for line in SpinLines:

            if CollectingInstructions:

                if line.endswith('/'):
                    CollectedInstructionLines.append(line.replace('/', ''))
                    CollectingInstructions = False

                else:
                    CollectedInstructionLines.append(line)

            if line.count(':') == 1:
                Param, Values = line.replace(' ', '').split(':')

                if Param == "name":
                    # If name is already set
                    if Name != '':
                        self.LLogger.LogError(
                            "WHEEL SPIN: Tried to declare a spin with multiple names: " + line)
                        Error = True
                        break

                    Name = Values

                elif Param == "atr":
                    for atr in Values.split(','):
                        if '=' in atr:

                            atr_name, atr_value_data = atr.split('=')

                            # Processing attribute types
                            if "[b]" in atr_value_data:
                                Atr[atr_name] = atr_value_data.replace('[b]', '').lower() == "true"

                            elif "[i]" in atr_value_data:
                                Atr[atr_name] = int(atr_value_data.replace('[i]', ''))

                            elif "[f]" in atr_value_data:
                                Atr[atr_name] = float(atr_value_data.replace('[f]', ''))

                            if "[s]" in atr_value_data:
                                Atr[atr_name] = atr_value_data.replace('[s]', '')

                        else:
                            Atr[atr] = True

                elif Param == "results":

                    for result in Values.split(','):
                        Results.append(result)

                elif Param == "instr":
                    CollectingInstructions = True
                    CollectedInstructionLines.append(Values)

        if len(Results) == 0:
            Error = True
            self.LLogger.LogError(f"WHEEL SPIN : Tried to declare a spin with no results : {Name}!")

        if not Error:

            # InName, InSpinsMin, InSpinsMax, InSpinSpeed, InResults

            SpinsMin = 20
            if "SpinsMin" in Atr:
                SpinsMin = Atr["SpinsMin"]

            SpinsMax = 40
            if "SpinsMax" in Atr:
                SpinsMax = Atr["SpinsMax"]

            SpinSpeed = 1
            if "SpinSpeed" in Atr:
                SpinSpeed = Atr["SpinSpeed"]

            SpinData = Spin(self, Name, SpinsMin, SpinsMax, SpinSpeed, Results)
            self.Spins[Name] = SpinData

            if len(CollectedInstructionLines) > 0:
                self.InstructionParsingQueue.put(Name)
                self.TransmitMessage("Instructions", "RE", {"Head": "INSTRUCTIONS_ParseInstructionCode",
                                                            "Data": {"Code": CollectedInstructionLines}})



    def InitPluginConfig(self):
        return self.InitOptionsConfig()

