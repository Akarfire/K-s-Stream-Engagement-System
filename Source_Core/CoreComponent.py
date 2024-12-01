class CoreComponent:

    def __init__(self, InCore, InLogSegmentName):
        self.MyCore = InCore
        self.LLogger = InCore.MyLogger

        self.LLogger.NewLogSegment(InLogSegmentName)

    def ReceivedData(self, InDataMessage):
        pass

    def TransmitData(self, OutDataMessage):
        pass
