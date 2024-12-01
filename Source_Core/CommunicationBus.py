from Source_Core.CoreComponent import CoreComponent
from Source_Core.AddressManagement import AddressManager
from Source_Core.Types import DataMessage


class CommunicationBus(CoreComponent):

    def __init__(self, InCore):
        super().__init__(InCore, "Init Communication Bus")

        self.MyAddressManager = AddressManager(self.MyCore.MyLogger)


    def ReceivedData(self, InDataMessage):
        self.TransmitData(InDataMessage)


    def TransmitData(self, OutDataMessage):

        if OutDataMessage.DataType in ["RE", "CB", "IN"]:
            if self.MyAddressManager.IsValidAddress(OutDataMessage.ReceiverAddress):
                self.MyAddressManager.GetComponent(OutDataMessage.ReceiverAddress).ReceivedData(OutDataMessage)

            else:
                self.LLogger.LogError(f"COMMUNICATION BUS: Invalid address: {OutDataMessage.ReceiverAddress}")

        if OutDataMessage.DataType == "EV":

            if self.MyAddressManager.IsValidEvent(OutDataMessage.Data["Head"]):
                for Rec in self.MyAddressManager.GetSubscribers(OutDataMessage.Data["Head"]):

                    NotificationMessage = DataMessage(Rec, OutDataMessage.SenderAddress, "EVN", OutDataMessage.Data)

                    if self.MyAddressManager.IsValidAddress(Rec):
                        self.MyAddressManager.GetComponent(Rec).ReceivedData(NotificationMessage)

                    else:
                        self.LLogger.LogError(
                            f"COMMUNICATION BUS: Invalid address: {Rec}")


    def RegisterAddress(self, InAddress, InComponent):
        self.MyAddressManager.RegisterAddress(InAddress, InComponent)
        self.LLogger.LogStatus(f"COMMUNICATION BUS: Registered address: {InAddress}")


    def RegisterSubscription(self, InEventName, InSubAddress):
        self.MyAddressManager.RegisterSubscription(InEventName, InSubAddress)


class CoreComponent_BusConnected(CoreComponent):

    def __init__(self, InCore, InAddress, InLogSegmentName):
        super().__init__(InCore, InLogSegmentName)

        self.Address = InAddress

        self.MyCommunicationBus = self.MyCore.MyCommunicationBus
        self.MyCommunicationBus.RegisterAddress(InAddress, self)


    def TransmitData(self, OutDataMessage):
        self.MyCommunicationBus.ReceivedData(OutDataMessage)