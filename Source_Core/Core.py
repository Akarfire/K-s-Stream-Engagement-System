from numpy.f2py.auxfuncs import throw_error

from Source_Core.Config import ConfigController
from Source_Core.Logger import  Logger
from Source_Core.ControlServer import ControlServer
from Source_Core.CommunicationBus import CommunicationBus
from Source_Core.PluginImpl import PluginManager
from Source_Core.InstructionProcessor import InstructionProcessor
import time
import Source_Core.CoreComponent

class CoreApp:

    def __init__(self):
        # Init Logger
        self.MyLogger = Logger()

        # Communication Bus
        self.MyCommunicationBus = CommunicationBus(self)

        # Init Config Controller
        self.MyConfigController = ConfigController(self, "Config", "Config")

        # Instruction Processor
        self.MyInstructionProcessor = InstructionProcessor(self, "Instructions")

        # Loading Plugins
        self.MyPluginManager = PluginManager(self, "Plugins")
        self.MyPluginManager.LoadPlugins()
        self.MyPluginManager.InitPlugins()

        # Control Server
        self.MyControlServer = ControlServer(self, "ControlServer")

        # Main Loop
        self.MyLogger.NewLogSegment("RUNTIME")

        self.TimeBetweenFrames = 1.0 / float(self.MyConfigController.Options["Main_Update_Frequency"])
        self.PreviousTime = time.time()
        self.DeltaTime = 0


    def MainLoop(self):
        try:
            while True:
                # Delta Time
                t = time.time()
                self.DeltaTime = t - self.PreviousTime
                self.PreviousTime = t

                # Runtime Logic
                self.MyPluginManager.UpdatePlugins(self.DeltaTime)
                #self.MyControlServer.UpdateControlServer()

                # Sleep
                time.sleep(self.TimeBetweenFrames)

        except Exception as e:
             self.MyLogger.LogError("CRASH DETECTED: " + str(e))
             pass

        # Quiting
        self.MyLogger.LogStatus("QUITING")
