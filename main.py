import TextToSpeech as tts
from ChatReader import ChatReader
from PyGameImplementation import PyGameWindow
from Config import ConfigController

import time

# Init PyGameWindow
MyPyGameWindow = PyGameWindow()

# Init Config Controller
MyConfigController = ConfigController(ConfigFolder="Config")

# Init TTS
MyTTS = tts.TTS()

# Init Chat Reader
MyChatReader = ChatReader(True, False, True, MyTTS, MyConfigController)

# Main Loop
while True:
    # Updating Pygame window
    if MyPyGameWindow.UpdatePyGameWindow():
        quit()
        exit()

    # Runtime Logic
    MyChatReader.UpdateChat()

    # Sleep
    time.sleep(1)


# Quiting
if (MyChatReader.USE_TWITCH):
    MyChatReader.TwitchSocket.close()

pygame.quit()


