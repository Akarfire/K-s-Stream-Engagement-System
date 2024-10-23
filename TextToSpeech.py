from gtts import gTTS
import pygame

class TTS:
    def __int__(self):
        self.slow = False

    # Converts text to speech using gTTS
    def ConvertTTS(self, txt, lg = 'en'):

        # Inits gTTS and converts
        MyTTS = gTTS(text=txt, lang=lg, slow=False)

        # Saves output to TTS_Audio.mp3
        MyTTS.save("TTS_Audio.mp3")

    def PlayTTS(self):

        # Plays last converetd TTS file
        Sound = pygame.mixer.Sound("TTS_Audio.mp3")
        Sound.play()