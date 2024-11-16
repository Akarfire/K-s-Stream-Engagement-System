from Source_Core.CoreComponent import CoreComponent
from Source_Core.AddressManagement import AddressManager
from Source_Core.Types import DataMessage


class CommunicationBus(CoreComponent):

    def __init__(self, InCore):
        super().__init__(InCore)

        self.MyAddressManager = AddressManager(self.MyCore.MyLogger)
        self.LLogger = self.MyCore.MyLogger


    def ReceivedData(self, InDataMessage):
        self.TransmitData(InDataMessage)


    def TransmitData(self, OutDataMessage):
        if self.MyAddressManager.IsValidAddress(OutDataMessage.ReceiverAddress):
            self.MyAddressManager.GetComponent(OutDataMessage.ReceiverAddress).ReceivedData(OutDataMessage)

        else:
            self.LLogger.LogError(f"COMMUNICATION BUS: Invalid address: {OutDataMessage.ReceiverAddress}")


    def RegisterAddress(self, InAddress, InComponent):
        self.MyAddressManager.RegisterAddress(InAddress, InComponent)



class CoreComponent_BusConnected(CoreComponent):

    def __init__(self, InCore, InAddress):
        super().__init__(InCore)
        self.MyCommunicationBus = self.MyCore.MyCommunicationBus
        self.MyCommunicationBus.RegisterAddress(InAddress, self)


    def TransmitData(self, OutDataMessage):
        self.MyCommunicationBus.ReceivedData(OutDataMessage)