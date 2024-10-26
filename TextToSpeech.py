from gtts import gTTS
import pygame

class TTS:
    def __int__(self):
        self.slow = False

    # Converts text to speech using gTTS
    def ConvertTTS(self, txt, lg = 'en'):

        if len(txt) > 0:
            try:
                # Inits gTTS and converts
                MyTTS = gTTS(text=txt, lang=lg, slow=False)

                # Saves output to TTS_Audio.mp3
                MyTTS.save("TmpFiles/TTS_Audio.mp3")
            except:
                print("Failed to TTS: ", txt)
                pass

    def PlayTTS(self):

        # Plays last converetd TTS file
        self.PlaySound("TmpFiles/TTS_Audio.mp3")

    def PlaySound(self, file):
        try:
            Sound = pygame.mixer.Sound(file)
            Sound.play()

        except:
            print("Failed to play sound")
            pass