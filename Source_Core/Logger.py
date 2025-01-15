import datetime
from pathlib import Path
import random
import Source_Core.Types

class Logger:

    def __init__(self):

        Path("Logs").mkdir(parents=True, exist_ok=True)
        self.Dir = "Logs/"
        self.FileName = "Log_" + datetime.datetime.now().strftime("%I_%M%p - %B_%d_%Y -- ") + str(random.randint(10000, 99999)) + ".txt"


    def LogString(self, InString, Print = True, Date = True):

        if Date:
            Now = datetime.datetime.now()
            Time = f"{Now.hour:02d}:{Now.minute:02d}:{Now.second:02d}.{str(Now.microsecond)[:2]}"
            LogLine = Time + "  :  " + InString

        else:
            LogLine = InString

        try:
            with open(self.Dir + self.FileName, 'a', encoding="utf-8") as File:
                File.write(LogLine + "\n")

        except Exception as e:
            self.LogError("Failed to write log file: " + str(e))
            pass

        if Print:
            print(LogLine)


    def LogMessage(self, InChatMessage):

        MessageStr = InChatMessage.Source + " -> " + InChatMessage.Author + ": " + InChatMessage.Message
        self.LogString(MessageStr)


    def LogObsResponse(self, InResponse):
        pass
        #self.LogString(str(InResponse), False)


    def LogStatus(self, InStatusMessage, Print = True):

        self.LogString(InStatusMessage, Print)


    def LogError(self, InErrorMessage):

        self.LogString("!ERROR! : " + InErrorMessage)


    def NewLogSegment(self, InSegmentName):

        LogLine = "\n---" + InSegmentName + "---" + "\n"
        self.LogString(LogLine, True, False)
