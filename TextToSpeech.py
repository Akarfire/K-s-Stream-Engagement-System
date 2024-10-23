from gtts import gTTS
import pygame

# Converts text to speech using gTTS
def ConvertTTS(txt, lg = 'en'):

    # Inits gTTS and converts
    MyTTS = gTTS(text=txt, lang=lg, slow=False)

    # Saves output to TTS_Audio.mp3
    MyTTS.save("TTS_Audio.mp3")


def PlayTTS():

    # Plays last converetd TTS file
    Sound = pygame.mixer.Sound("TTS_Audio.mp3")
    Sound.play()