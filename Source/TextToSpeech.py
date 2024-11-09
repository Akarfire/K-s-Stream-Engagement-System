from gtts import gTTS
import pygame

class TTS:
    def __init__(self, InConfigController, InLogger):
        self.slow = False
        self.LConfigController = InConfigController
        self.LLogger = InLogger

        self.LLogger.NewLogSegment("Init TTS")


    # Converts text to speech using gTTS
    def ConvertTTS(self, txt, lg = 'en'):

        if len(txt) > 0:
            try:
                # Inits gTTS and converts
                MyTTS = gTTS(text=txt, lang=lg, slow=False)

                # Saves output to TTS_Audio.mp3
                MyTTS.save("TmpFiles/TTS_Audio.mp3")
            except:
                self.LLogger.LogError("Failed to TTS: ", txt)
                pass


    def PlayTTS(self):

        # Plays last converetd TTS file
        return self.PlaySound("TmpFiles/TTS_Audio.mp3", self.LConfigController.Options["TTS_Volume"])


    def PlaySound(self, file, Volume = 1.0):
        try:
            Sound = pygame.mixer.Sound(file)
            Sound.set_volume(Volume)
            Sound.play()

            return Sound.get_length()

        except:
            self.LLogger.LogError("Failed to play sound")
            return 0


