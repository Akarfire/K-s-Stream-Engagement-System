from Source import TextToSpeech as tts
from Source.ChatReader import ChatReader
from Source.PyGameImplementation import PyGameWindow
from Source.Config import ConfigController
from Source.Commands import CommandProcessor
from Source.OBS_Interface import ObsInterface
import time

# Init PyGameWindow
MyPyGameWindow = PyGameWindow()

# Init Config Controller
MyConfigController = ConfigController(ConfigFolder="Config")

# Init TTS
MyTTS = tts.TTS(MyConfigController)

# Init OBS Interface
MyObsInterface = ObsInterface(MyConfigController)

# Init Command Processor
MyCommandProcessor = CommandProcessor(MyConfigController, MyTTS, MyObsInterface)

# Init Chat Reader
MyChatReader = ChatReader(MyConfigController, MyCommandProcessor)


# Main Loop
TimeBetweenFrames = 1.0 / float(MyConfigController.Options["Main_Update_Frequency"])
PreviousTime = time.time()
DeltaTime = 0

while True:
    # Updating Pygame window
    if MyPyGameWindow.UpdatePyGameWindow():
        quit()
        exit()

    # Delta Time
    t = time.time()
    DeltaTime = t - PreviousTime
    PreviousTime = t

    # Runtime Logic
    #MyChatReader.UpdateChat()
    MyCommandProcessor.UpdateCommandExecution(DeltaTime)

    # Sleep
    time.sleep(TimeBetweenFrames)


# Quiting
if (MyChatReader.USE_TWITCH):
    MyChatReader.TwitchSocket.close()

pygame.quit()


