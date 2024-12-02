from numpy.f2py.auxfuncs import throw_error

class AddressManager:

    def __init__(self, InLogger):
        self.Addresses = dict() # <address, component>
        self.Subscriptions = dict() # <event, list[addresses]>
        self.LLogger = InLogger


    def RegisterAddress(self, InAddress, InComponent):

        if not InAddress in self.Addresses:
            self.Addresses[InAddress] = InComponent

        else:
            self.LLogger.LogError(f"ADDRESS MANAGER: Address '{InAddress}' is already registered!")


    def GetComponent(self, InAddress):

        if InAddress in self.Addresses:
            return self.Addresses[InAddress]

        else:
            self.LLogger.LogError(f"ADDRESS MANAGER: Address '{InAddress}' does not exist!")


    def IsValidAddress(self, InAddress):

        return InAddress in self.Addresses


    def RegisterSubscription(self, InEventName, InReceiverAddress):

        if InEventName in self.Subscriptions:
            if not InReceiverAddress in self.Subscriptions[InEventName]:
                self.Subscriptions[InEventName].append(InReceiverAddress)

        else:
            self.Subscriptions[InEventName] = [InReceiverAddress]


    def GetSubscribers(self, InEventName):

        if InEventName in self.Subscriptions:
            return self.Subscriptions[InEventName]

        else:
            self.LLogger.LogError(f"SUBSCRIPTION MANAGER: Event '{InEventName}' does not exist!")


    def IsValidEvent(self, InEventName):

        return InEventName in self.Subscriptions




