
from ChatReader import TwitchAuthData

class ConfigController:
    def __init__(self, ConfigFolder):

        # Twitch Chat Data
        FileTwitchAuthData = open(ConfigFolder + "/TWITCH_AUTH.txt")
        TwitchAuthDataRead = [str(i) for i in FileTwitchAuthData.readlines()]

        self.TwitchAuth = TwitchAuthData(
            server="irc.chat.twitch.tv",
            port=6667,
            nickname=TwitchAuthDataRead[0],
            token=TwitchAuthDataRead[1],
            channel=TwitchAuthDataRead[2]
        )

        FileTwitchAuthData.close()

        # YT Chat Data
        YtUrlFile = open(ConfigFolder + "/YT_URL.txt")

        self.YT_Url = YtUrlFile.readline()

        YtUrlFile.close()