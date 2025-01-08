from logging import exception
from threading import Event

from cx_Freeze import Executable
from numpy.f2py.symbolic import Language

from Source_Core import PluginImpl
from gtts import gTTS
import pygame
from pathlib import Path
import pyttsx3
import librosa
import soundfile


class TextToSpeech(PluginImpl.PluginBase):

    def __init__(self, InPluginManager):
        super().__init__(InPluginManager, "Init PLUGIN: Text To Speech")

        self.Address = "TextToSpeech"
        self.ConfigSection = "TTS"
        self.Subscriptions = []
        self.Instructions = [ ("TTS_ConvertTTS", {}), ("TTS_PlayTTS", {}), ("TTS_PlaySFX", {}) ]

        self.display = None
        self.clock = None
        self.slow = None
        self.FinishEventTimers = dict()

        self.AddOption("Use_TTS", True)
        self.AddOption("TTS_Volume", 1.0)
        self.AddOption("SFX_Volume", 1.0)

        self.TTS_FilePath = "TmpFiles/TTS_Audio.mp3"


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

        try:
            # Update pygame
            for event in pygame.event.get():
                # Quit Condition
                if event.type == pygame.QUIT:
                    pygame.quit()

            # Frame Updates
            pygame.display.update()
            self.clock.tick(60)

        except Exception as e:
            self.LLogger.LogError(f"TTS: Pygame update error : '{e}'!")


    def ReceiveMessage(self, InDataMessage):

        super().ReceiveMessage(InDataMessage)

        if InDataMessage.DataType == "IN":
            if InDataMessage.Data["Head"] == "TTS_ConvertTTS":
                self.ConvertTTS(InDataMessage.Data["Data"]["Text"], InDataMessage.Data["Data"]["Engine"], InDataMessage.Data["Data"])

            elif InDataMessage.Data["Head"] == "TTS_PlayTTS":
                Time = self.PlayTTS()
                self.FinishEventTimers[InDataMessage.Data["Data"]["UID"]] = {"Event" : "TTS_FinishedPlayingTTS", "Timer" : Time}

            elif InDataMessage.Data["Head"] == "TTS_PlaySFX":
                Time = self.PlaySound(InDataMessage.Data["Data"]["File"], InDataMessage.Data["Data"]["Volume"] * self.GetOption("SFX_Volume"))
                self.FinishEventTimers[InDataMessage.Data["Data"]["UID"]] = {"Event": "TTS_FinishedPlayingSFX", "Timer": Time}


    # Converts text to speech using gTTS
    def ConvertTTS(self, InText, InEngine, InAllParameters):

        Text = InText.replace('\n', ' ').replace('\r', ' ')
        if self.GetOption("Use_TTS") and len(InText) > 0:
            try:

                # GTTS
                if InEngine == "GTTS":
                    self.ConvertGTTS(Text, InAllParameters)

                elif InEngine == "PyTTS":
                    self.ConvertPyTTS(Text, InAllParameters)

                self.ProcessTTSAudio(InAllParameters)

            except Exception as e:
                self.LLogger.LogError(f"Failed to TTS: '{Text}' with Engine '{InEngine}' and parameters: {str(InAllParameters)}! :: {str(e)}")
                pass


    def ConvertGTTS(self, InText, InAllParameters):

        Language = "en"
        if "Language" in InAllParameters:
            Language = InAllParameters["Language"]

        # Inits gTTS and converts
        MyTTS = gTTS(text=InText, lang=Language, slow=False)

        # Saves output to TTS_Audio.mp3
        MyTTS.save(self.TTS_FilePath)


    def ConvertPyTTS(self, InText, InAllParameters):

        Converter = pyttsx3.init()

        Rate = 200
        if "Rate" in InAllParameters:
            Rate = InAllParameters["Rate"]

        Volume = 1
        if "Volume" in InAllParameters:
            Volume = InAllParameters["Volume"]

        Converter.setProperty("rate", Rate)
        Converter.setProperty("volume", Volume)

        VoiceID = 1
        if "VoiceID" in InAllParameters:
            VoiceID = InAllParameters["VoiceID"]

        Voices = Converter.getProperty("voices")
        Converter.setProperty("voice", Voices[VoiceID].id)

        Converter.save_to_file(InText, self.TTS_FilePath)
        Converter.runAndWait()


    def ProcessTTSAudio(self, InAllParameters):

        # Pitch Shift

        PitchShiftSteps = 0
        if "PitchShiftSteps" in InAllParameters:
            PitchShiftSteps = InAllParameters["PitchShiftSteps"]

        if PitchShiftSteps != 0:

            Y, Sr = librosa.load(self.TTS_FilePath)
            New_Y = librosa.effects.pitch_shift(Y, sr=Sr, n_steps=PitchShiftSteps, bins_per_octave=24)
            soundfile.write(self.TTS_FilePath, New_Y, Sr)


    def PlayTTS(self):

        if self.GetOption("Use_TTS"):
            # Plays last convereted TTS file
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