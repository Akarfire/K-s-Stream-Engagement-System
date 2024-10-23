import TextToSpeech as TTS
import pygame

# Init PyGame
pygame.init()
pygame.mixer.pre_init(44100, 16, 2, 4096) # Frequency, channel size, channels, buffersize
pygame.mixer.init()
display = pygame.display.set_mode((400, 40))
pygame.display.set_caption("K's Super TTS")
clock = pygame.time.Clock()

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
    clock.tick(1/10)

    # Runtime Logic
    TTS.ConvertTTS("Hello Chat!")
    TTS.PlayTTS()


# Quiting
pygame.quit()


