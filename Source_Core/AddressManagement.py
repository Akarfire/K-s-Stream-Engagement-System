from numpy.f2py.auxfuncs import throw_error

class AddressManager:

    def __init__(self, InLogger):
        self.Addresses = dict() # <address, component>
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



class SubscriptionManager:

    def __init__(self, InLogger):
        self.Subscriptions = dict() # <event, list[core_component]>



