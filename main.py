from Source_Core import TextToSpeech as tts
from Source_Core.ChatReader import ChatReader
from Source_Core.PyGameImplementation import PyGameWindow
from Source_Core.Config import ConfigController
from Source_Core.Commands import CommandProcessor
from Source_Core.OBS_Interface import ObsInterface
from Source_Core.Logger import  Logger
from Source_Core.ControlServer import ControlServer
import time

# Init Logger
MyLogger = Logger()

# Init PyGameWindow
MyPyGameWindow = PyGameWindow()

# Init Config Controller
MyConfigController = ConfigController("Config", MyLogger)

# Init TTS
MyTTS = tts.TTS(MyConfigController, MyLogger)

# Init OBS Interface
MyObsInterface = ObsInterface(MyConfigController, MyLogger)

# Init Command Processor
MyCommandProcessor = CommandProcessor(MyConfigController, MyTTS, MyObsInterface, MyLogger)

# Init Chat Reader
MyChatReader = ChatReader(MyConfigController, MyCommandProcessor, MyLogger)

# Control Server
MyControlServer = ControlServer(MyLogger, MyCommandProcessor)


# Main Loop
MyLogger.NewLogSegment("RUNTIME")

TimeBetweenFrames = 1.0 / float(MyConfigController.Options["Main_Update_Frequency"])
PreviousTime = time.time()
DeltaTime = 0

try:
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
            MyChatReader.MainThreadUpdate()
            MyCommandProcessor.UpdateCommandExecution(DeltaTime)
            MyControlServer.UpdateControlServer()

            # Sleep
            time.sleep(TimeBetweenFrames)

except Exception as e:
    MyLogger.LogError("CRASH DETECTED: " + str(e))
    pass

# Quiting
MyLogger.LogStatus("QUITING")

if (MyChatReader.USE_TWITCH):
    MyChatReader.TwitchSocket.close()
try:
    pygame.quit()

except:
    pass
