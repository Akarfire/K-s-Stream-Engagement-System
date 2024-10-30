import pygame

# Init PyGame

class PyGameWindow:
    def __init__(self):
        pygame.init()
        #pygame.mixer.pre_init(44100, 16, 2, 4096)
        pygame.mixer.init()
        self.display = pygame.display.set_mode((400, 40))
        pygame.display.set_caption("K's Super TTS")
        self.clock = pygame.time.Clock()


    def UpdatePyGameWindow(self):
        for event in pygame.event.get():
            # Quit Condition
            if event.type == pygame.QUIT:
                pygame.quit()
                return True

        # Frame Updates
        pygame.display.update()
        self.clock.tick(60)

        return False