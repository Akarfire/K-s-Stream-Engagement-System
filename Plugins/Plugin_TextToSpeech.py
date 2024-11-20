from threading import Event

from Source_Core import PluginImpl
from gtts import gTTS
import pygame
from pathlib import Path


class TextToSpeech(PluginImpl.PluginBase):

    def __init__(self, InPluginManager):
        super().__init__(InPluginManager)

        self.Address = "TextToSpeech"
        self.ConfigSection = "TTS"
        self.Subscriptions = []
        self.Instructions = ["TTS_ConvertTTS", "TTS_PlayTTS", "TTS_PlaySFX"]

        self.display = None
        self.clock = None
        self.slow = None
        self.LLogger = None
        self.FinishEventTimers = dict()

        self.AddOption("Use_TTS", True)
        self.AddOption("TTS_Volume", 1.0)
        self.AddOption("SFX_Volume", 1.0)


    def InitPlugin(self):
        super().InitPlugin()

        # Pygame Init
        pygame.init()
        # pygame.mixer.pre_init(44100, 16, 2, 4096)
        pygame.mixer.init()
        self.display = pygame.display.set_mode((400, 40))
        pygame.display.set_caption("K's Super TTS")
        self.clock = pygame.time.Clock()

        self.slow = False
        self.LLogger = self.MyPluginManager.LLogger

        # Create SFX Directory
        Path("SFX").mkdir(parents=True, exist_ok=True)
        Path("TmpFiles").mkdir(parents=True, exist_ok=True)


    def DeletePlugin(self):
        pass


    def UpdatePlugin(self, DeltaSeconds):

        # Update finished event timers
        TimersToFinish = []
        for EventTimer in self.FinishEventTimers:

            self.FinishEventTimers[EventTimer]["Timer"] -= DeltaSeconds

            if  self.FinishEventTimers[EventTimer]["Timer"] <= 0:

                self.TransmitEvent(self.FinishEventTimers[EventTimer]["Event"], {"UID" : EventTimer})
                TimersToFinish.append(EventTimer)

        for Timer in TimersToFinish:
            self.FinishEventTimers.pop(Timer)

        # Update pygame
        for event in pygame.event.get():
            # Quit Condition
            if event.type == pygame.QUIT:
                pygame.quit()

        # Frame Updates
        pygame.display.update()
        self.clock.tick(60)


    def ReceiveMessage(self, InDataMessage):

        super().ReceiveMessage(InDataMessage)

        if InDataMessage.DataType == "IN":
            if InDataMessage.Data["Head"] == "TTS_ConvertTTS":
                self.ConvertTTS(InDataMessage.Data["Data"])

            elif InDataMessage.Data["Head"] == "TTS_PlayTTS":
                Time = self.PlayTTS()
                self.FinishEventTimers[InDataMessage.Data["Data"]["UID"]] = {"Event" : "TTS_FinishedPlayingTTS", "Timer" : Time}

            elif InDataMessage.Data["Head"] == "TTS_PlaySFX":
                Time = self.PlaySound(InDataMessage.Data["Data"]["File"], InDataMessage.Data["Data"]["Volume"] * self.GetOption("SFX_Volume"))
                self.FinishEventTimers[InDataMessage.Data["Data"]["UID"]] = {"Event": "TTS_FinishedPlayingSFX", "Timer": Time}


    # Converts text to speech using gTTS
    def ConvertTTS(self, txt, lg='en'):

        if self.GetOption("Use_TTS") and len(txt) > 0:
            try:
                # Inits gTTS and converts
                MyTTS = gTTS(text=txt, lang=lg, slow=False)

                # Saves output to TTS_Audio.mp3
                MyTTS.save("TmpFiles/TTS_Audio.mp3")
            except:
                self.LLogger.LogError("Failed to TTS: " + txt)
                pass


    def PlayTTS(self):

        if self.GetOption("Use_TTS"):
            # Plays last converetd TTS file
            return self.PlaySound("TmpFiles/TTS_Audio.mp3", self.GetOption("TTS_Volume"))


    def PlaySound(self, file, Volume=1.0):

        try:
            Sound = pygame.mixer.Sound(file)
            Sound.set_volume(Volume)
            Sound.play()

            return Sound.get_length()

        except:
            self.LLogger.LogError("Failed to play sound")
            return 0