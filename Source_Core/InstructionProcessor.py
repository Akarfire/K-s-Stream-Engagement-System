from dis import Instruction

from Source_Core.CommunicationBus import CoreComponent_BusConnected
from Source_Core.Types import DataMessage

class InstructionMacro:
    def __init__(self, InMacroName = "", InCode = ""):
        self.MacroName = InMacroName
        self.Arguments = set()
        self.Code = InCode

class InstructionProcessor(CoreComponent_BusConnected):

    def __init__(self, InCore, InAddress):
        super().__init__(InCore, InAddress)

        self.LLogger = InCore.MyLogger
        self.Instructions = dict()
        self.Macros = dict()

        MacroRequestMessage = DataMessage("Config", self.Address, "RE", { "Head" : "PluginConfigRequest", "Data" : {"ConfigSection" : "InstructionMacro"} })
        self.TransmitData(MacroRequestMessage)


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


        elif InDataMessage.DataType == "CB" and InDataMessage.Data["Head"] == "PluginConfigRequest":
            self.ParseMacroCode(InDataMessage.Data["Data"]["ConfigLines"])


    def ParseMacroCode(self, InCode):

        InCode.append('-')

        CurrentMacroData = InstructionMacro()

        InstructionSection = False
        InstructionCode = ""
        for Line in InCode:
            Line = Line.replace(' ', '').replace('  ', '').replace('\n', '')

            if InstructionSection:
                if Line.endswith('/'):
                    InstructionCode += Line.replace('/', '')
                    CurrentMacroData.Code = InstructionCode
                    continue

                InstructionCode += Line

            elif Line == '-':
                if CurrentMacroData.MacroName != "":
                    self.Macros[CurrentMacroData.MacroName] = CurrentMacroData

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

        Code = Code.replace('\n', '').replace(' ', '').replace('    ', '')

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

        CurrentHeader = {"Name" : "Default", "Type" : "BLOCK"}
        CurrentInstructions = []

        CurrentLexeme = ""
        while len(Code) > 0:
            for i in Code:

                if i == '{':
                    IsHeaderValid, CurrentHeader = self.ParseHeader(CurrentLexeme)

                    if not IsHeaderValid:
                        self.LLogger.LogError(f"INSTRUCTION PARSING: Invalid header in '{CurrentLexeme}'!")
                        return dict()

                    if CurrentHeader in OutParsedCode:
                        self.LLogger.LogError(f"INSTRUCTION PARSING: Header '{CurrentHeader}' already exists!")
                        return dict()

                    Code = Code.replace(CurrentLexeme + i, '', 1)
                    CurrentLexeme = ""
                    break

                elif i == '}':
                    if len(CurrentLexeme) > 0:
                        self.LLogger.LogError(f"INSTRUCTION PARSING: ';' expected after every instruction!")
                        return dict()

                    OutParsedCode[CurrentHeader] = CurrentInstructions
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
            return True, {"Name" : HeaderName, "Type" : HeaderType}

        if ':' in InLex:
            HeaderType, HeaderName = InLex.split(':', 1)

        # Validation
        Valid = True

        for i in HeaderName:
            if not i in "QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890_":
                Valid = False
                break

        if not HeaderType in ["BLOCK", "EVENT"]:
            Valid = False

        if not Valid:
            return False, {"Name" : HeaderName, "Type" : HeaderType}


    def ParseInstruction(self, InLex):

        if len(InLex) == 0:
            self.LLogger.LogError("INSTRUCTION PARSING: Emtpy instruction!")
            return False, dict()

        if not '(' in InLex or (InLex.count('(') != InLex.count(')')):
            self.LLogger.LogError(f"INSTRUCTION PARSING: Incorrect brackets (or no brackets) in instruction lexeme '{InLex}'!")
            return False, dict()

        InstructionName, ArgumentsStr = InLex.split('(', 1)
        ArgumentsStr = ArgumentsStr.replace(')', ',')

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
            self.LLogger.LogError("INSTRUCTION PARSING: Emtpy argument!")
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
            ArgumentValue = ArgumentValueStr


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

            UnwrappedCode = UnwrappedCode.replace('$' + Arg + '$', InMacro["Arguments"][Arg])


        return UnwrappedCode



