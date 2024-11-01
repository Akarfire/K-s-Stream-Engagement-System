
from Source.Types import Command

# def fCommand_TTS(InTTS, InChatMessage):
#     if len(InChatMessage.Message) > 0:
#         InTTS.ConvertTTS(InChatMessage.Message)
#         return InTTS.PlayTTS()
#
# def fCommand_PlaySound(InTTS, InSoundFile, InVolume = 1.0):
#     return InTTS.PlaySound(InSoundFile, InTTS.LConfigController.Options["SFX_Volume"] * InVolume)



class Command_TTS(Command):
    def ExecuteCommand(self, InChatMessage):
        if len(InChatMessage.Message) > 0:
            self.Processor.TTS.ConvertTTS(InChatMessage.Message)

            self.FinishOnTimer = True
            self.Timer = self.Processor.TTS.PlayTTS()

    def FinishExecution(self):
        super().FinishExecution()


class Command_PlaySound(Command):
    def ExecuteCommand(self, InChatMessage):
        self.FinishOnTimer = True

        Volume = 1.0
        if "volume" in self.Atr:
            Volume = self.Atr["volume"]

        if "file" in self.Atr:
            self.Timer = self.Processor.TTS.PlaySound("SFX/" + self.Atr["file"], self.Processor.LConfigController.Options["SFX_Volume"] * Volume)

        else:
            self.Timer = self.Processor.TTS.PlaySound("SFX/" + self.Name + ".mp3", self.Processor.LConfigController.Options["SFX_Volume"] * Volume)

    def FinishExecution(self):
        super().FinishExecution()


