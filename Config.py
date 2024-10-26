from numpy.f2py.auxfuncs import throw_error
from select import select
from ChatReader import TwitchAuthData
from Types import Command

class ConfigController:
    def __init__(self, ConfigFolder):

        # Default Values
        self.TwitchAuth = TwitchAuthData("", 0, "", "", "")
        self.YT_Url = ""

        # Options Map
        self.Options = \
            {
            "Use_YT" : False,
            "Use_Twitch" : False,
            "Filter_Tolerance" : 0.85,
            "TTS_Volume" : 1.0,
            "SFX_Volume" : 1.0,
            }

        self.TWITCH_DataFound = False
        self.YT_DataFound = False

        # Command Map:
        self.Commands = {}

        # Twitch Chat Data
        self.ReadTwitchData(ConfigFolder + "/TWITCH_AUTH.txt")

        # YT Chat Data
        self.ReadYTCData(ConfigFolder + "/YT_URL.txt")

        # Config Data
        self.ReadConfigData(ConfigFolder + "/Config.txt")


    def ReadTwitchData(self, Path):
        print ("Reading Twitch data at: ", Path)

        try:
            FileTwitchAuthData = open(Path)
            DataFound = True

        except:
            print("'", Path, "'", " doesn't exist, creating now")
            FileTwitchAuthData = open(Path, 'w')
            FileTwitchAuthData.write(
                "nickname: \n\
                token: oauth: \n\
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
            print("\nTwitch Data cannot be read, pls check the config file!\n")



    def ReadYTCData(self, Path):
        print("Reading YT data at: ", Path)
        try:
            YtUrlFile = open(Path)
            DataFound = True

        except:
            print("'", Path, "'", " doesn't exist, creating now")
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
            print("\nYouTube Data cannot be read, pls check the config file!\n")



    def ReadConfigData(self, Path):
        print("Reading Config data at: ", Path)
        try:
            ConfigFile = open(Path)

        except:
            print("'", Path, "'", " doesn't exist, creating now")
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
                    if len(OptionLine) > 0 and OptionLine.count(':') == 2:
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
        Name, ValueType, Value = OptionLine.replace(' ', '').split(':')

        if ValueType == 'b':
            self.Options[Name] = Value == "true"

        elif ValueType == 'i':
            self.Options[Name] = int(Value)

        elif ValueType == 'f':
            self.Options[Name] = float(Value)

        elif ValueType == 's':
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
                        Calls.add(call)

                if Param == "atr":
                    for atr in Values.split(','):
                        if '=' in atr:

                            atr_name, atr_value_data = atr.split('=')

                            # Processing attribute types
                            if "[b]" in atr_value_data:
                                Atr[atr_name] = atr_value_data.replace('[b]', '') == "true"

                            elif "[i]" in atr_value_data:
                                Atr[atr_name] = int(atr_value_data.replace('[i]', ''))

                            elif "[f]" in atr_value_data:
                                Atr[atr_name] = float(atr_value_data.replace('[f]', ''))

                            if "[s]" in atr_value_data:
                                Atr[atr_name] = atr_value_data.replace('[s]', '')

                        else:
                            Atr[atr] = True

        self.Commands[Name] = Command(Name, Calls, Atr)


    def InitConfigFile(self, Path):
        print("Initializing Config File")

        ConfigFile = open(Path, 'w')
        ConfigFile.write(
            "\
            <Config>\n\
            K's Stream Engagement System V0.1\n\
            ---------------------------------\n\
            #Options\n\
            Use_YT: b: true\n\
            Use_Twitch: b: true\n\
            \n\
            Filter_Tolerance: f: 0.85\n\
            \n\
            TTS_Volume: f: 1.0\n\
            SFX_Volume: f: 1.0\n\
            #\n\
            \n\
            #Commands\n\
            #\n".replace('  ', '')
        )
        ConfigFile.close()

