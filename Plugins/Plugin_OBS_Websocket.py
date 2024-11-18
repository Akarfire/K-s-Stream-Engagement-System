from Source_Core import PluginImpl
import websocket
import base64
import hashlib
import json
from dataclasses import dataclass

@dataclass
class ObsAuthData:
    host : str
    port : int
    password : str

class ObsWebsocket(PluginImpl.PluginBase):

    def __init__(self):
        super().__init__()

        self.Address = "ObsWebsocket"
        self.ConfigSection = "OBS"
        self.Subscriptions = []
        self.Instructions = ["OBS_SetFilterEnabled", "OBS_SetItemEnabled"]

        self.ObsAuth = ObsAuthData("localhost", 4455, "password")


    def InitPlugin(self, InPluginManager):
        super().InitPlugin(InPluginManager)

        # Data
        self.LConfigController = self.MyCore.MyConfigController
        self.AuthData = self.LConfigController.ObsAuth

        self.LLogger = self.MyCore.MyLogger

        self.Enabled = self.LConfigController.OBS_DataFound and self.LConfigController.Options["Use_OBS"]

        if self.Enabled:

            url = "ws://{}:{}".format(self.AuthData.host, self.AuthData.port)
            self.ObsWS = websocket.WebSocket()

            try:
                self.ObsWS.connect(url)

                # Authentication
                self.Authenticate()

            except Exception as e:
                self.LLogger.LogError("Failed to connect to OBS: " + str(e))
                self.Enabled = False
                pass

        else:
            self.LLogger.LogStatus("OBS integration disabled")

    def DeletePlugin(self):
        pass

    def UpdatePlugin(self, DeltaSeconds):
        pass

    def ReceiveMessage(self, InDataMessage):

        super().ReceiveMessage(InDataMessage)

        if self.Enabled:
            if InDataMessage.DataType == "IN":

                if InDataMessage.Data["Head"] == "OBS_SetFilterEnabled":
                    Data = InDataMessage.Data["Data"]
                    self.SetFilterEnabled(Data["Source"], Data["Filter"], Data["NewEnabled"])

                elif InDataMessage.Data["Head"] == "OBS_SetItemEnabled":
                    Data = InDataMessage.Data["Data"]
                    self.SetItemEnabledByName(Data["Scene"], Data["Item"], Data["NewEnabled"])


    def GenerateAuthString(self, Challenge, Salt):

        Base64Secret = base64.b64encode(hashlib.sha256((self.AuthData.password + Salt).encode("utf-8")).digest())
        Auth = base64.b64encode(hashlib.sha256(Base64Secret + Challenge.encode("utf-8")).digest()).decode("utf-8")

        return Auth


    def Authenticate(self):

        # Hello message
        HelloMsg = self.ObsWS.recv()
        Res = json.loads(HelloMsg)

        # Identify message
        Auth = self.GenerateAuthString(Res['d']["authentication"]["challenge"], Res['d']["authentication"]["salt"])

        Payload = {
              "op": 1,
              "d": {
                "rpcVersion": 1,
                "authentication": Auth,
                "eventSubscriptions": 0
              }
            }

        # Identified message
        self.ObsWS.send(json.dumps(Payload))
        Response = self.ObsWS.recv()
        self.LLogger.LogObsResponse(json.loads(Response))


    def SendRequest(self, RequestType, RequestID, RequestData):

        if self.Enabled:
            Payload = {
                "op": 6,
                "d": {
                    "requestType": RequestType,
                    "requestId": RequestID,
                    "requestData": RequestData
                }
            }

            self.ObsWS.send(json.dumps(Payload))
            Response  = self.ObsWS.recv()

            return json.loads(Response)

        else:
            return "OBS Interface Disabled"


    def SwitchScene(self, SceneName):

        Response = self.SendRequest("SetCurrentProgramScene", "SetScene", {"sceneName" : SceneName})
        self.LLogger.LogObsResponse(Response)


    def GetItemID(self, Scene, Item):

        Response = self.SendRequest("GetSceneItemId", "GetItemID", {
            "sceneName": Scene,
            "sourceName": Item
        })

        return Response["d"]["responseData"]["sceneItemId"]


    def SetItemEnabledByID(self, Scene, ItemID, NewEnabled):

        Response = self.SendRequest("SetSceneItemEnabled", "SetItemEnabled", {
            "sceneName": Scene,
            "sceneItemId": ItemID,
            "sceneItemEnabled": NewEnabled
        })

        self.LLogger.LogObsResponse(Response)


    def SetItemEnabledByName(self, Scene, Item, NewEnabled):

        self.SetItemEnabledByID(Scene, self.GetItemID(Scene, Item), NewEnabled)


    def SetFilterEnabled(self, Source, Filter, NewEnabled):

        Response = self.SendRequest("SetSourceFilterEnabled", "SetFilterEnabled", {
            "sourceName" : Source,
            "filterName" : Filter,
            "filterEnabled" : NewEnabled
        })

        self.LLogger.LogObsResponse(Response)


    def ReadConfigData(self, InConfigFileLines):

        self.ReadOptions(InConfigFileLines)

        Path = "Config/OBS_AUTH.txt"
        self.LLogger.LogStatus("Reading OBS data at: " + Path)
        try:
            ObsDataFile = open(Path)
            DataFound = True

        except:
            self.LLogger.LogStatus(f"'{Path}' doesn't exist, creating now")
            ObsDataFile = open(Path, 'w')
            ObsDataFile.write("host: localhost\nport: 4455\npassword: ")
            ObsDataFile.close()

            DataFound = False
            pass

        if DataFound:
            ObsAuthDataLines = ObsDataFile.readlines()

            if len(ObsAuthDataLines) >= 3:

                try:
                    self.ObsAuth.host = ObsAuthDataLines[0].replace("host: ", '')
                    self.ObsAuth.port = int(ObsAuthDataLines[1].replace("port: ", ''))
                    self.ObsAuth.password = ObsAuthDataLines[2].replace("password: ", '')

                    self.OBS_DataFound = True

                except:
                    self.LLogger.LogError("Invalid Obs Auth Data")
                    self.OBS_DataFound = False
                    pass