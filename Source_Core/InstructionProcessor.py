from dis import Instruction

from Source_Core.CommunicationBus import CoreComponent_BusConnected
from Source_Core.Types import DataMessage, InstructionCodeHeader



class InstructionMacro:
    def __init__(self, InMacroName = "", InCode = ""):
        self.MacroName = InMacroName
        self.Arguments = set()
        self.Code = InCode



class RuntimeParameter:
    def __init__(self, InParameterName):
        self.Name = InParameterName


class InstructionProcessor(CoreComponent_BusConnected):

    def __init__(self, InCore, InAddress):
        super().__init__(InCore, InAddress, "Init Instruction Processor")

        self.Instructions = dict()
        self.Macros = dict()

        MacroRequestMessage = DataMessage("Config", self.Address, "RE", { "Head" : "PluginConfigRequest", "Data" : {"ConfigSection" : "InstructionMacro"} })
        self.TransmitData(MacroRequestMessage)

        # Registering Core instructions
        self.RegisterInstruction("FLOW_RunSection_IF_EQ", "CORE")
        self.RegisterInstruction("FLOW_RunSection_IF_NotEQ", "CORE")


    def RegisterInstruction(self, InInstructionName, InExecutorAddress, InMeta = None):

        if InMeta == None:
            InMeta = dict()

        if not InInstructionName in self.Instructions:
            self.Instructions[InInstructionName] = {"Executor" : InExecutorAddress, "Meta" : InMeta.copy()}
            self.MyCore.MyLogger.LogStatus(f"INSTRUCTION PROCESSOR: Registered Instruction: '{InInstructionName}'")

        else:
            self.MyCore.MyLogger.LogError(f"INSTRUCTION PROCESSOR: Instruction '{InInstructionName}' is already registered for {self.Instructions[InInstructionName]}!")


    def ExecuteCoreInstruction(self, InInstruction, InArguments, InCallerAddress, InRuntimeParameters):

        # Execute section if L == R
        if InInstruction == "FLOW_RunSection_IF_EQ":

            if not "Code" in InRuntimeParameters:
                self.LLogger.LogError(
                    f"INSTRUCTION FLOW: {InInstruction} failed to execute: no Code in runtime parameters!")

            if "L" in InArguments and "R" in InArguments and "Section" in InArguments and "Code" in InRuntimeParameters:
                Section = InArguments["Section"]
                if Section in InRuntimeParameters["Code"]:

                    if InArguments["L"] == InArguments["R"]:
                        self.InterpretInstructions(InRuntimeParameters["Code"][Section]["Instructions"],
                                                   InCallerAddress, InRuntimeParameters)
                else:
                    self.LLogger.LogError(
                        f"INSTRUCTION FLOW: {InInstruction} failed to execute: invalid code section: {Section}!")
            else:
                self.LLogger.LogError(
                    f"INSTRUCTION FLOW: {InInstruction} failed to execute: invalid arguments!")

        # Execute section if L != R
        if InInstruction == "FLOW_RunSection_IF_NotEQ":

            if not "Code" in InRuntimeParameters:
                self.LLogger.LogError(
                    f"INSTRUCTION FLOW: {InInstruction} failed to execute: no Code in runtime parameters!")

            if "L" in InArguments and "R" in InArguments and "Section" in InArguments and "Code" in InRuntimeParameters:
                Section = InArguments["Section"]
                if Section in InRuntimeParameters["Code"]:

                    if InArguments["L"] != InArguments["R"]:
                        self.InterpretInstructions(InRuntimeParameters["Code"][Section]["Instructions"],
                                                   InCallerAddress, InRuntimeParameters)
                else:
                    self.LLogger.LogError(
                        f"INSTRUCTION FLOW: {InInstruction} failed to execute: invalid code section: {Section}!")
            else:
                self.LLogger.LogError(
                    f"INSTRUCTION FLOW: {InInstruction} failed to execute: invalid arguments!")


    def ReceivedData(self, InDataMessage):

        if InDataMessage.DataType == "IN":

            if InDataMessage.Data["Head"] == "INSTRUCTIONS_InterpretInstructions":
                self.InterpretInstructions(InDataMessage.Data["Data"]["Instructions"], InDataMessage.SenderAddress, InDataMessage.Data["Data"]["RuntimeParameters"])

            elif InDataMessage.Data["Head"] in self.Instructions:
                self.RunInstruction(InDataMessage.Data["Head"], InDataMessage.Data["Data"], InDataMessage.SenderAddress, {})

                # Executor = self.Instructions[InDataMessage.Data["Head"]]
                #
                # if Executor == "CORE":
                #     self.ExecuteCoreInstruction(InDataMessage.Data["Head"], InDataMessage.Data["Data"])
                #
                # else:
                #     InstructionCallMessage = DataMessage(Executor, InDataMessage.SenderAddress, "IN", InDataMessage.Data)
                #     self.TransmitData(InstructionCallMessage)


        elif InDataMessage.DataType == "CB" and InDataMessage.Data["Head"] == "PluginConfigRequest":
            self.ParseMacroCode(InDataMessage.Data["Data"]["ConfigLines"])

        elif InDataMessage.DataType == "RE" and InDataMessage.Data["Head"] == "INSTRUCTIONS_ParseInstructionCode":
            ParsedCode = self.ParseInstructionCode(InDataMessage.Data["Data"]["Code"])

            CallBackMessage = DataMessage(InDataMessage.SenderAddress, self.Address, "CB", {"Head" : "INSTRUCTIONS_ParseInstructionCode", "Data" : {"Instructions" : ParsedCode}})
            self.TransmitData(CallBackMessage)


    def RunInstruction(self, InInstruction, InArguments, CallerAddress, InRuntimeParameters):

        try:
            if not InInstruction in self.Instructions:
                self.LLogger.LogError(f"INSTRUCTIONS: Invalid instruction '{InInstruction}'!")
                return

            Executor = self.Instructions[InInstruction]["Executor"]

            if "RequestAllRuntimeParameters" in self.Instructions[InInstruction]["Meta"]:
                if self.Instructions[InInstruction]["Meta"]["RequestAllRuntimeParameters"]:
                    InArguments["RuntimeParameters"] = InRuntimeParameters

            if Executor == "CORE":
                self.ExecuteCoreInstruction(InInstruction, InArguments, CallerAddress, InRuntimeParameters)

            else:
                InstructionCallMessage = DataMessage(Executor, CallerAddress, "IN", {"Head" : InInstruction, "Data" : InArguments})
                self.TransmitData(InstructionCallMessage)

        except Exception as e:
            self.LLogger.LogError(f"INSTRUCTION EXECUTION: {InInstruction} failed to execute: {e}")


    def InterpretInstructions(self, InInstructions, InCallerAddress, InRuntimeParameters):

        for Instr in InInstructions:
            self.RunInstruction(Instr["Instruction"], self.InterpretArguments(Instr["Arguments"], InRuntimeParameters), InCallerAddress, InRuntimeParameters)


    def InterpretArguments(self, InArguments, InRuntimeParameters):

        OutArguments = dict()

        for Arg in InArguments:

            if type(InArguments[Arg]) == RuntimeParameter:
                if InArguments[Arg].Name in InRuntimeParameters:
                    OutArguments[Arg] = InRuntimeParameters[InArguments[Arg].Name]
                else:
                    OutArguments[Arg] = None

            else:
                OutArguments[Arg] = InArguments[Arg]

        return OutArguments


    def ParseMacroCode(self, InCode):

        InCode.append('-')
        CurrentMacroData = InstructionMacro()

        InstructionSection = False
        InstructionCode = ""
        for Line in InCode:
            Line = Line.replace(' ', '').replace('\t', '').replace('\n', '')

            if InstructionSection:
                if Line.endswith('/'):
                    InstructionCode += Line.replace('/', '')
                    CurrentMacroData.Code = InstructionCode
                    InstructionCode = ""
                    InstructionSection = False
                    continue

                InstructionCode += Line

            if Line == '-':
                if CurrentMacroData.MacroName != "":
                    self.Macros[CurrentMacroData.MacroName] = CurrentMacroData
                    CurrentMacroData = InstructionMacro()

            elif Line.startswith("name:"):
                CurrentMacroData.MacroName = Line.replace("name:", '')

            elif Line.startswith("args:"):
                for Arg in Line.replace("args:", '').split(','):
                    CurrentMacroData.Arguments.add(Arg)

            elif Line.startswith("instr:"):
                InstructionSection = True
                InstructionCode += Line.replace("instr:", '')


    def ParseInstructionCode(self, InCode):
        # InCode is a list of Code Lines, we will turn it into a monolith line
        Code = ""
        for L in InCode:
            Code += L

        Code = Code.replace('\n', '').replace(' ', '').replace('\t', '')

        # MACRO IMPLEMENTATION
        while '$' in Code:
            MacroStart = Code.index('$')

            MacroEnd = MacroStart + 1
            while Code[MacroEnd] != '$':
                if MacroEnd >= len(Code):
                    self.LLogger.LogError(f"INSTRUCTION PARSING: Unbound macro in '{Code}'")
                    return dict()

                MacroEnd += 1

            MacroCode = Code[MacroStart + 1 : MacroEnd]
            IsMacroCodeValid, Macro = self.ParseInstruction(MacroCode)

            IsMacroValid = IsMacroCodeValid and Macro["Instruction"] in self.Macros

            if not IsMacroValid:
                self.LLogger.LogError(f"INSTRUCTION PARSING: Invalid macro in '{MacroCode}'")
                return dict()

            Code = Code.replace('$' + MacroCode + '$', self.UnwrapMacro(Macro))

        # PARSING
        OutParsedCode = dict()

        CurrentHeader = InstructionCodeHeader("Default", "BLOCK") #{"Name" : "Default", "Type" : "BLOCK"}
        CurrentInstructions = []

        CurrentLexeme = ""
        while len(Code) > 0:
            for i in Code:

                if i == '{':
                    IsHeaderValid, CurrentHeader = self.ParseHeader(CurrentLexeme)


                    if not IsHeaderValid:
                        self.LLogger.LogError(f"INSTRUCTION PARSING: Invalid header in '{CurrentLexeme}'!")
                        return dict()

                    if (CurrentHeader.Type + "_" + CurrentHeader.Name) in OutParsedCode:
                        self.LLogger.LogError(f"INSTRUCTION PARSING: Header '{CurrentHeader}' already exists!")
                        return dict()

                    Code = Code.replace(CurrentLexeme + i, '', 1)
                    CurrentLexeme = ""
                    break

                elif i == '}':
                    if len(CurrentLexeme) > 0:
                        self.LLogger.LogError(f"INSTRUCTION PARSING: ';' expected after every instruction!")
                        return dict()

                    OutParsedCode[CurrentHeader.Type + "_" + CurrentHeader.Name] = { "Header" : CurrentHeader, "Instructions" : CurrentInstructions.copy()}
                    CurrentInstructions.clear()
                    Code = Code.replace(i, '', 1)
                    break

                elif i == ';':
                    IsInstructionValid, Instruction = self.ParseInstruction(CurrentLexeme)

                    if not IsInstructionValid:
                        self.LLogger.LogError(f"INSTRUCTION PARSING: Invalid instruction in '{CurrentLexeme}'!")
                        return dict()

                    CurrentInstructions.append(Instruction)
                    Code = Code.replace(CurrentLexeme + i, '', 1)
                    CurrentLexeme = ""
                    break

                CurrentLexeme += i

            else:
                self.LLogger.LogError(f"INSTRUCTION PARSING: Unbound / Unfinished statement in '{CurrentLexeme}'!")
                return dict()


        return OutParsedCode


    def ParseHeader(self, InLex):

        HeaderName = "Default"
        HeaderType = "BLOCK"

        if len(InLex) == 0:
            return True, InstructionCodeHeader(HeaderName, HeaderType)

        if ':' in InLex:
            HeaderType, HeaderName = InLex.split(':', 1)

        else:
            HeaderName = InLex

        # Validation
        Valid = True

        for i in HeaderName:
            if not i in "QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890_":
                Valid = False
                break

        if not HeaderType in ["BLOCK", "EVENT"]:
            Valid = False

        if not Valid:
            return False, InstructionCodeHeader(HeaderName, HeaderType)

        return True, InstructionCodeHeader(HeaderName, HeaderType)


    def ParseInstruction(self, InLex):

        if len(InLex) == 0:
            self.LLogger.LogError("INSTRUCTION PARSING: Empty instruction!")
            return False, dict()

        if not '(' in InLex or (InLex.count('(') != InLex.count(')')):
            self.LLogger.LogError(f"INSTRUCTION PARSING: Incorrect brackets (or no brackets) in instruction lexeme '{InLex}'!")
            return False, dict()

        InstructionName, ArgumentsStr = InLex.split('(', 1)
        ArgumentsStr = ArgumentsStr.replace(')', '')

        if len(ArgumentsStr) > 0:
            ArgumentsStr += ','

        Arguments = dict()
        CurrentArgument = ""
        while len(ArgumentsStr) > 0:
            for i in ArgumentsStr:

                if i == ',':
                    IsValidArgument, ArgumentName, ArgumentValue = self.ParseArgument(CurrentArgument)

                    if not IsValidArgument:
                        self.LLogger.LogError(f"INSTRUCTION PARSING: Incorrect argument in '{InLex}' : '{CurrentArgument}'!")
                        return False, dict()

                    Arguments[ArgumentName] = ArgumentValue
                    ArgumentsStr = ArgumentsStr.replace(CurrentArgument + i, '', 1)
                    CurrentArgument = ""
                    break

                CurrentArgument += i

            else:
                break

        return True, {"Instruction" : InstructionName, "Arguments" : Arguments}


    def ParseArgument(self, InLex):

        if len(InLex) == 0:
            self.LLogger.LogError("INSTRUCTION PARSING: Empty argument!")
            return False, "", None

        if InLex.count('=') != 1:
            self.LLogger.LogError(f"INSTRUCTION PARSING: Wrong / None '=' signs in argument '{InLex}'")
            return False, "", None

        ArgumentName, ArgumentValueStr = InLex.split('=')

        ArgumentValue = None

        if "[b]" in ArgumentValueStr:
            ArgumentValue = ArgumentValueStr.replace('[b]', '').lower() == "true"

        elif "[i]" in ArgumentValueStr:
            ArgumentValue = int(ArgumentValueStr.replace('[i]', ''))

        elif "[f]" in ArgumentValueStr:
            ArgumentValue = float(ArgumentValueStr.replace('[f]', ''))

        elif "[s]" in ArgumentValueStr:
            ArgumentValue = ArgumentValueStr.replace('[s]', '')

        else:
            ArgumentValue = RuntimeParameter(ArgumentValueStr)


        return True, ArgumentName, ArgumentValue


    def UnwrapMacro(self, InMacro):

        if not InMacro["Instruction"] in self.Macros:
            self.LLogger.LogError(f"INSTRUCTION PARSING: Invalid macro '{InMacro}'")
            return ""

        MacroData = self.Macros[InMacro["Instruction"]]
        UnwrappedCode = MacroData.Code

        for Arg in MacroData.Arguments:

            if not Arg in InMacro["Arguments"]:
                self.LLogger.LogError(f"INSTRUCTION PARSING: Required argument '{Arg}' not found in macro code '{InMacro}'")
                return ""

            UnwrappedCode = UnwrappedCode.replace('$' + Arg + '$', '[' + type(InMacro["Arguments"][Arg]).__name__[0] + ']' + str(InMacro["Arguments"][Arg]))


        return UnwrappedCode



