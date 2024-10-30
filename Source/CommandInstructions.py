
def Command_TTS(InTTS, InChatMessage):
    if len(InChatMessage.Message) > 0:
        InTTS.ConvertTTS(InChatMessage.Message)
        InTTS.PlayTTS()

def Command_PlaySound(InTTS, InSoundFile, InVolume = 1.0):
    InTTS.PlaySound(InSoundFile, InTTS.LConfigController.Options["SFX_Volume"] * InVolume)
