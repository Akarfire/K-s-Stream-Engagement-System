import datetime
from mailbox import Message

import Source_Core.Types

class Logger:

    def __init__(self):

        self.Dir = "Logs/"
        self.FileName = "Log_" + datetime.datetime.now().strftime("%I_%M%p - %B_%d_%Y") + ".txt"

        #self.File = open(self.Dir + self.FileName, 'w')

    # def __del__(self):
    #     self.File.close()


    def LogString(self, InString, Print = True):

        Time = datetime.datetime.now().strftime("%I:%M%p - %B_%d_%Y")
        LogLine = Time + "  :  " + InString

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

        self.LogString(str(InResponse), False)


    def LogStatus(self, InStatusMessage, Print = True):

        self.LogString(InStatusMessage, Print)


    def LogError(self, InErrorMessage):

        self.LogString("!ERROR! : " + InErrorMessage)


    def NewLogSegment(self, InSegmentName):

        LogLine = "\n---" + InSegmentName + "---" + "\n"
        self.LogString(LogLine)
