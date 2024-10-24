import TextToSpeech as tts
import pygame
import time

from ChatReader import ChatReader, TwitchAuthData

# Init PyGame
pygame.init()
pygame.mixer.pre_init(44100, 16, 2, 4096)
pygame.mixer.init()
display = pygame.display.set_mode((400, 40))
pygame.display.set_caption("K's Super TTS")
clock = pygame.time.Clock()

# Init TTS
MyTTS = tts.TTS()

# Read YT link from file
YT_Url_File = open("YT_Url.txt")
YT_Url = YT_Url_File.readline()
YT_Url_File.close()

# Init Chat Reader
MyChatReader = ChatReader(True, MyTTS, True, YT_Url, True, "MyTwitchAuthData.txt")

# Main Loop
while True:
    for event in pygame.event.get():

        # Quit Condition
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
            exit()

    # Frame Updates
    pygame.display.update()
    clock.tick(60)

    # Runtime Logic
    MyChatReader.UpdateChat()

    # Sleep
    time.sleep(1)


# Quiting
pygame.quit()


