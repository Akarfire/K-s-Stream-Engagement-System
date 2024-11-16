from Source_Core import TextToSpeech as tts
from Source_Core.ChatReader import ChatReader
from Source_Core.PluginImpl import LoadPlugins, PluginBase
from Source_Core.PyGameImplementation import PyGameWindow
from Source_Core.Config import ConfigController
from Source_Core.Commands import CommandProcessor
from Source_Core.OBS_Interface import ObsInterface
from Source_Core.Logger import  Logger
from Source_Core.ControlServer import ControlServer
from Source_Core.CommunicationBus import CommunicationBus
from Source_Core.PluginImpl import PluginManager
import time
import Source_Core.CoreComponent

class CoreApp:

    def __init__(self):
        # Init Logger
        self.MyLogger = Logger()

        # Communication Bus
        self.MyCommunicationBus = CommunicationBus(self)

        # Loading Plugins
        self.MyPluginManager = PluginManager(self, "PluginManager")

        self.MyPluginManager.LoadPlugins()

        # Init Config Controller
        self.MyConfigController = ConfigController("Config", self.MyLogger)

        # Init PyGameWindow
        self.MyPyGameWindow = PyGameWindow()

        # Init TTS
        self.MyTTS = tts.TTS(self.MyConfigController, self.MyLogger)

        # Init OBS Interface
        self.MyObsInterface = ObsInterface(self.MyConfigController, self.MyLogger)

        # Init Command Processor
        self.MyCommandProcessor = CommandProcessor(self.MyConfigController, self.MyTTS, self.MyObsInterface, self.MyLogger)

        # Init Chat Reader
        #self.MyChatReader = ChatReader(self.MyConfigController, self.MyCommandProcessor, self.MyLogger)

        # Init Plugins
        self.MyPluginManager.InitPlugins()

        # Control Server
        self.MyControlServer = ControlServer(self.MyLogger, self.MyCommandProcessor)

        # Main Loop
        self.MyLogger.NewLogSegment("RUNTIME")

        self.TimeBetweenFrames = 1.0 / float(self.MyConfigController.Options["Main_Update_Frequency"])
        self.PreviousTime = time.time()
        self.DeltaTime = 0


    def MainLoop(self):
        try:
            while True:
                # Updating Pygame window
                if self.MyPyGameWindow.UpdatePyGameWindow():
                    quit()
                    exit()

                # Delta Time
                t = time.time()
                self.DeltaTime = t - self.PreviousTime
                self.PreviousTime = t

                # Runtime Logic
                for Plugin in self.Plugins:
                    Plugin.UpdatePlugin(self.DeltaTime)

                #self.MyChatReader.MainThreadUpdate()
                self.MyCommandProcessor.UpdateCommandExecution(self.DeltaTime)
                self.MyControlServer.UpdateControlServer()

                # Sleep
                time.sleep(self.TimeBetweenFrames)

        except Exception as e:
            self.MyLogger.LogError("CRASH DETECTED: " + str(e))
            pass

        # Quiting
        self.MyLogger.LogStatus("QUITING")

        try:
            pygame.quit()

        except:
            pass
