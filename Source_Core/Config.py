from numpy.f2py.auxfuncs import throw_error
from select import select
from Source_Core.Types import Command, TwitchAuthData, ObsAuthData
from Source_Core.Commands import AssignCommand

class ConfigController:
    def __init__(self, ConfigFolder, InLogger):

        self.LLogger = InLogger
        self.LLogger.NewLogSegment("Loading Config Data")

        # Default Values
        self.TwitchAuth = TwitchAuthData("", 0, "", "", "")
        self.YT_Url = ""
        self.ObsAuth = ObsAuthData("localhost", 4455, "password")

        # Options Map
        self.DefaultOptions = \
            {
            "Use_YT" : True,
            "Use_Twitch" : True,
            "Use_OBS" : True,
            "Filter_Tolerance" : 0.85,
            "TTS_Volume" : 1.0,
            "SFX_Volume" : 1.0,
            "Update_Frequency" : 4,
            "Chat_Fetch_Frequency" : 4
            }

        self.Options = self.DefaultOptions

        self.TWITCH_DataFound = False
        self.YT_DataFound = False
        self.OBS_DataFound = False

        # Command Map:
        self.Commands = {}

        # Twitch Chat Data
        self.ReadTwitchData(ConfigFolder + "/TWITCH_AUTH.txt")

        # YT Chat Data
        self.ReadYTData(ConfigFolder + "/YT_URL.txt")

        # OBS Auth Data
        self.ReadObsData(ConfigFolder + "/OBS_AUTH.txt")

        # Config Data
        self.ReadConfigData(ConfigFolder + "/Config.txt")


    def ReadTwitchData(self, Path):
        self.LLogger.LogStatus("Reading Twitch data at: " + Path)

        try:
            FileTwitchAuthData = open(Path)
            DataFound = True

        except:
            self.LLogger.LogStatus("'" + Path + "'" + " doesn't exist, creating now")
            FileTwitchAuthData = open(Path, 'w')
            FileTwitchAuthData.write(
                "nickname: \n\
                token: \n\
                channel: ".replace('    ', '')
            )
            FileTwitchAuthData.close()

            DataFound = False
            pass

        if DataFound:
            TwitchData = FileTwitchAuthData.readlines()

            if len(TwitchData) >= 3:
                self.TwitchAuth = TwitchAuthData(
                    server="irc.chat.twitch.tv",
                    port=6667,
                    nickname=TwitchData[0].replace('nickname: ', ''),
                    token=TwitchData[1].replace('token: ', ''),
                    channel=TwitchData[2].replace('channel: ', '')
                )
                FileTwitchAuthData.close()

                self.TWITCH_DataFound = True

        else:
            self.LLogger.LogError("Twitch Data cannot be read, pls check the config file!")


    def ReadYTData(self, Path):
        self.LLogger.LogStatus("Reading YT data at: " + Path)
        try:
            YtUrlFile = open(Path)
            DataFound = True

        except:
            self.LLogger.LogStatus("'" + Path + "'" + " doesn't exist, creating now")
            YtUrlFile = open(Path, 'w')
            YtUrlFile.write("YT_url: ")
            YtUrlFile.close()

            DataFound = False
            pass

        if DataFound:
            YTData = YtUrlFile.readlines()
            if len(YTData) > 0:
                self.YT_Url = YTData[0].replace("YT_url: ", '')

            YtUrlFile.close()

            self.YT_DataFound = True

        else:
            self.LLogger.LogError("YouTube Data cannot be read, pls check the config file!")


    def ReadObsData(self, Path):
        self.LLogger.LogStatus("Reading OBS data at: " + Path)
        try:
            ObsDataFile = open(Path)
            DataFound = True

        except:
            self.LLogger.LogStatus("'" + Path + "'" + " doesn't exist, creating now")
            ObsDataFile = open(Path, 'w')
            ObsDataFile.write("host: localhost\nport: 4455\npassword: ")
            ObsDataFile.close()

            DataFound = False
            pass

        if DataFound:
            ObsAuthDataLines = ObsDataFile.readlines()

            if len(ObsAuthDataLines) >= 3:

                try:
                    self.ObsAuth.host = ObsAuthDataLines[0].replace("host: ", '')
                    self.ObsAuth.port = int(ObsAuthDataLines[1].replace("port: ", ''))
                    self.ObsAuth.password = ObsAuthDataLines[2].replace("password: ", '')

                    self.OBS_DataFound = True

                except:
                    self.LLogger.LogError("Invalid Obs Auth Data")
                    self.OBS_DataFound = False
                    pass


    def ReadConfigData(self, Path):
        self.LLogger.LogStatus("Reading Config data at: " + Path)
        try:
            ConfigFile = open(Path)

        except:
            self.LLogger.LogStatus("'", Path, "'", " doesn't exist, creating now")
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
            # First, we split it into 2 sections: Options and Commands
            if "#Options" in ConfigLines:

                i = ConfigLines.index("#Options") + 1
                while ConfigLines[i] != '#' and i < len(ConfigLines):\

                    OptionLine = ConfigLines[i]
                    if len(OptionLine) > 0 and OptionLine.count('=') == 1:
                        self.ProcessOptionLine(OptionLine)

                    i += 1

            # Now to read the commands
            if "#Commands" in ConfigLines:

                CurrentCommandLines = []
                i = ConfigLines.index("#Commands") + 1
                while ConfigLines[i] != '#' and i < len(ConfigLines):
                    if ConfigLines[i] != '':

                        if ConfigLines[i].replace(' ', '') == '-':
                            self.ProcessCommandLines(CurrentCommandLines)
                            CurrentCommandLines = []

                        else:
                            CurrentCommandLines.append(ConfigLines[i])

                    i += 1

                if len(CurrentCommandLines) > 0:
                    self.ProcessCommandLines(CurrentCommandLines)


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


    def ProcessCommandLines(self, CommandLines):
        Name = ""
        Calls = set()
        Atr = {}

        for line in CommandLines:
            if line.count(':') == 1:
                Param, Values = line.replace(' ', '').split(':')

                if Param == "name":
                    # If name is already set
                    if Name != '':
                        throw_error("Tried to declare a command with multiple names: " + line)

                    Name = Values
                    Calls.add(Name)

                if Param == "calls":
                    for call in Values.split(','):
                        Calls.add(call.upper())

                if Param == "atr":
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

        self.Commands[Name] = AssignCommand(Name, Calls, Atr)


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

