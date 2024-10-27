from Source import TextToSpeech as tts
from Source.ChatReader import ChatReader
from Source.PyGameImplementation import PyGameWindow
from Source.Config import ConfigController
from Source.Commands import CommandProcessor
import time

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


