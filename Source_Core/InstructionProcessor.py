from Source_Core.CommunicationBus import CoreComponent_BusConnected
from Source_Core.Types import DataMessage


class InstructionProcessor(CoreComponent_BusConnected):

    def __init__(self, InCore, InAddress):
        super().__init__(InCore, InAddress)

        self.Instructions = dict()


    def RegisterInstruction(self, InInstructionName, InExecutorAddress):

        if not InInstructionName in self.Instructions:
            self.Instructions[InInstructionName] = InExecutorAddress
            self.MyCore.MyLogger.LogStatus(f"INSTRUCTION PROCESSOR: Registered Instruction: '{InInstructionName}'")

        else:
            self.MyCore.MyLogger.LogError(f"INSTRUCTION PROCESSOR: Instruction '{InInstructionName}' is already registered for {self.Instructions[InInstructionName]}!")


    def ExecuteCoreInstruction(self, InInstruction, InArguments):
        pass


    def ReceivedData(self, InDataMessage):

        if InDataMessage.DataType == "IN":
            if InDataMessage.Data["Head"] in self.Instructions:
                # Instr = InDataMessage.Data["Head"]
                # self.MyCore.MyLogger.LogStatus(f"INSTRUCTION PROCESSOR: Received Instruction: '{Instr}'")
                Executor = self.Instructions[InDataMessage.Data["Head"]]

                if Executor == "CORE":
                    self.ExecuteCoreInstruction(InDataMessage.Data["Head"], InDataMessage.Data["Data"])

                else:
                    InstructionCallMessage = DataMessage(Executor, InDataMessage.SenderAddress, "IN", InDataMessage.Data)
                    self.TransmitData(InstructionCallMessage)