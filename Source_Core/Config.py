from numpy.f2py.auxfuncs import throw_error
from select import select
from traitlets.config import Config

from Source_Core.Types import DataMessage
from Source_Core.CommunicationBus import CoreComponent_BusConnected
from pathlib import Path

class ConfigController(CoreComponent_BusConnected):

    def __init__(self, InCore, InAddress, ConfigFolder):
        super().__init__(InCore, InAddress, "Loading Config Data")

        self.Path = ConfigFolder

        # Options Map
        self.DefaultOptions = \
            {
            "Main_Update_Frequency" : 4,
            }

        self.Options = self.DefaultOptions
        self.PluginConfigSegments = dict()

        # Creating Directory
        Path(ConfigFolder).mkdir(parents=True, exist_ok=True)

        # Config Data
        self.ReadConfigData(ConfigFolder + "/Config.txt")


    def ReceivedData(self, InDataMessage):

        if InDataMessage.DataType == "RE":

            if InDataMessage.Data["Head"] == "PluginConfigRequest":
                ConfigSection = InDataMessage.Data["Data"]["ConfigSection"]

                if ConfigSection != "":
                    if ConfigSection in self.PluginConfigSegments:
                        CallBackMessage = DataMessage(InDataMessage.SenderAddress, self.Address, "CB", {"Head" : "PluginConfigRequest", "Data" : {"ConfigLines" : self.PluginConfigSegments[ConfigSection]}})
                        self.TransmitData(CallBackMessage)

                    else:
                        InitConfigRequestMessage = DataMessage(InDataMessage.SenderAddress, self.Address, "RE", {"Head" : "PluginInitConfigRequest", "Data" : {}})
                        self.TransmitData(InitConfigRequestMessage)

            elif InDataMessage.Data["Head"] == "RequestAllOptions":
                CallbackMessage = DataMessage(InDataMessage.SenderAddress, self.Address, "CB", {"Head" : "RequestAllOptions", "Data" : { "Options" : self.Options }})
                self.TransmitData(CallbackMessage)


        elif InDataMessage.DataType == "CB" and InDataMessage.Data["Head"] == "PluginInitConfigRequest":
            self.InitConfigSection(InDataMessage.Data["Data"]["ConfigSectionName"], InDataMessage.Data["Data"]["ConfigLines"])

            CallBackMessage = DataMessage(InDataMessage.SenderAddress, self.Address, "CB",
                                          {"Head": "PluginConfigRequest",
                                           "Data": {"ConfigLines": self.PluginConfigSegments[InDataMessage.Data["Data"]["ConfigSectionName"]]}})
            self.TransmitData(CallBackMessage)


    def ReadConfigData(self, Path):
        self.LLogger.LogStatus("Reading Config data at: " + Path)
        try:
            ConfigFile = open(Path)

        except:
            self.LLogger.LogStatus(f"'{Path}' doesn't exist, creating now")
            self.InitConfigFile(Path)
            ConfigFile = open(Path)
            pass

        ConfigLines = [i.replace('\n', '') for i in ConfigFile.readlines()]
        ConfigFile.close()

        if len(ConfigLines) > 0:
            # Check if the file is valid
            if ConfigLines[0] != "<Config>":
                self.InitConfigFile(Path)

            # Now, when the file is valid we can read it
            # First, we read Core Options
            if "#Core" in ConfigLines:
                i = ConfigLines.index("#Core") + 1
                while ConfigLines[i] != '#' and i < len(ConfigLines):\

                    OptionLine = ConfigLines[i]
                    if len(OptionLine) > 0 and OptionLine.count('=') == 1:
                        self.ProcessOptionLine(OptionLine)

                    i += 1

            # Then we read plugin configs
            CurrentConfigSection = ""
            CurrentSectionLines = []
            for i in range(len(ConfigLines)):

                if CurrentConfigSection != "" and ConfigLines[i].count('#') == 0:
                    CurrentSectionLines.append(ConfigLines[i])

                elif ConfigLines[i].count('#') == 1:

                    if CurrentConfigSection != "":
                        self.PluginConfigSegments[CurrentConfigSection] = CurrentSectionLines.copy()
                        CurrentConfigSection = ""
                        CurrentSectionLines.clear()

                    if len(ConfigLines[i].replace('#', '')) > 0:
                        CurrentConfigSection = ConfigLines[i].replace('#', '').replace('\n', '')

            if CurrentConfigSection != "":
                self.PluginConfigSegments[CurrentConfigSection] = CurrentSectionLines

        ConfigFile.close()


    def ProcessOptionLine(self, OptionLine):
        Name, Value = OptionLine.replace(' ', '').split('=')

        if '[b]' in Value:
            self.Options[Name] = Value.replace('[b]', '').lower() == "true"

        elif '[i]' in Value:
            self.Options[Name] = int(Value.replace('[i]', ''))

        elif '[f]' in Value:
            self.Options[Name] = float(Value.replace('[f]', ''))

        elif '[s]' in Value:
            self.Options[Name] = Value.replace('[s]', '')

        else:
            self.Options[Name] = Value



    def InitConfigFile(self, Path):
        self.LLogger.LogStatus("Initializing Config File")

        OptionLines = ""
        for i in self.DefaultOptions:
            OptionLines += i + " = " +'[' + type(self.DefaultOptions[i]).__name__[0] + ']' + str(self.DefaultOptions[i]).lower() + "\n"

        ConfigFile = open(Path, 'w')
        ConfigFile.write(
            ("\
            <Config>\n\
            K's Stream Engagement System V0.1\n\
            ---------------------------------\n\
            #Options\n\n" + \
            OptionLines + "\n\
            #\n\
            \n\
            #Commands\n\
            #\n").replace('  ', '')
        )
        ConfigFile.close()


    def InitConfigSection(self, InSectionName, InSectionLines):
        self.PluginConfigSegments[InSectionName] = InSectionLines

        ConfigFile = open(self.Path + "/Config.txt", "a")

        ConfigFile.write("\n#" + InSectionName + "\n")
        for i in InSectionLines:
            ConfigFile.write(i)
        ConfigFile.write("#\n")

        ConfigFile.close()

