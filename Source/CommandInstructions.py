
from Source.Types import Command


class Command_TTS(Command):
    def ExecuteCommand(self, InChatMessage):
        if len(InChatMessage.Message) > 0:
            self.Processor.TTS.ConvertTTS(InChatMessage.Message)

            self.FinishOnTimer = True
            self.Timer = self.Processor.TTS.PlayTTS() + 0.5

            # GLady Avatar
            self.Processor.LObsInterface.SetFilterEnabled("GLadyAvatar", "Silent", False)

    def FinishExecution(self):

        self.Processor.LObsInterface.SetFilterEnabled("GLadyAvatar", "Silent", True)
        super().FinishExecution()


class Command_PlaySound(Command):
    def ExecuteCommand(self, InChatMessage):
        self.FinishOnTimer = True
        self.GifName = ""

        Volume = 1.0
        if "volume" in self.Atr:
            Volume = self.Atr["volume"]

        if "file" in self.Atr:
            self.Timer = self.Processor.TTS.PlaySound("SFX/" + self.Atr["file"], self.Processor.LConfigController.Options["SFX_Volume"] * Volume)

        else:
            self.Timer = self.Processor.TTS.PlaySound("SFX/" + self.Name + ".mp3", self.Processor.LConfigController.Options["SFX_Volume"] * Volume)

        if "time" in self.Atr:
            self.Timer = self.Atr["time"]

        if "obs_gif" in self.Atr:
            self.GifName = self.Name

            if "obs_gif_name" in self.Atr:
                self.GifName = self.Atr["obs_gif_name"]

            self.Processor.LObsInterface.SetItemEnabledByName("GIFscene", self.GifName, True)


    def FinishExecution(self):

        if self.GifName != "":
            self.Processor.LObsInterface.SetItemEnabledByName("GIFscene", self.GifName, False)

        super().FinishExecution()


