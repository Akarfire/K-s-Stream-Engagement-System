import TextToSpeech as tts
from ChatReader import ChatReader
from PyGameImplementation import PyGameWindow
from Config import ConfigController
from Commands import CommandProcessor

import time

from Types import ChatMessage

# Init PyGameWindow
MyPyGameWindow = PyGameWindow()

# Init Config Controller
MyConfigController = ConfigController(ConfigFolder="Config")

# Init TTS
MyTTS = tts.TTS(MyConfigController)

# Init Command Processor
MyCommandProcessor = CommandProcessor(MyConfigController, MyTTS)

# Init Chat Reader
MyChatReader = ChatReader(MyConfigController, MyCommandProcessor)

# Main Loop
while True:
    # Updating Pygame window
    if MyPyGameWindow.UpdatePyGameWindow():
        quit()
        exit()

    # Runtime Logic
    MyChatReader.UpdateChat()
    MyCommandProcessor.UpdateCommandExecution(0.5)

    # Sleep
    time.sleep(0.5)


# Quiting
if (MyChatReader.USE_TWITCH):
    MyChatReader.TwitchSocket.close()

pygame.quit()


