import TextToSpeech as tts
from ChatReader import ChatReader
from PyGameImplementation import PyGameWindow
from Config import ConfigController
from Commands import CommandProcessor

import time

# Init PyGameWindow
MyPyGameWindow = PyGameWindow()

# Init Config Controller
MyConfigController = ConfigController(ConfigFolder="Config")

# Init Command Processor
MyCommandProcessor = CommandProcessor(MyConfigController)
print(MyCommandProcessor.ScanMessageForCommands("Hey there, !voi ce!"))

# Init TTS
MyTTS = tts.TTS()

# Init Chat Reader
MyChatReader = ChatReader(MyConfigController, MyTTS)

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


