import datetime
from pathlib import Path
import Source_Core.Types

class Logger:

    def __init__(self):

        Path("Logs").mkdir(parents=True, exist_ok=True)
        self.Dir = "Logs/"
        self.FileName = "Log_" + datetime.datetime.now().strftime("%I_%M%p - %B_%d_%Y") + ".txt"


    def LogString(self, InString, Print = True, Date = True):

        if Date:
            Time = datetime.datetime.now().strftime("%I:%M%p - %B_%d_%Y")
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
