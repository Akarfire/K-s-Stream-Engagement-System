import websocket
import base64
import hashlib
import json

from Source.Types import ObsAuthData

class ObsInterface:
    def __init__(self, InConfigController):

        # Data
        self.LConfigController = InConfigController
        self.AuthData = InConfigController.ObsAuth

        self.Enabled = InConfigController.OBS_DataFound and InConfigController.Options["Use_OBS"]

        if self.Enabled:

            url = "ws://{}:{}".format(self.AuthData.host, self.AuthData.port)
            self.ObsWS = websocket.WebSocket()
            self.ObsWS.connect(url)

            # Authentication
            self.Authenticate()

        else:
            print("OBS integration disabled")


    def __del__(self):
        pass
        #if self.Enabled:
            #self.ObsWS.close()


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
        print(json.loads(Response))


    def SendRequest(self, RequestType, RequestID, RequestData = {}):

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
        #print(Response)


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

        #print(Response)


    def SetItemEnabledByName(self, Scene, Item, NewEnabled):
        self.SetItemEnabledByID(Scene, self.GetItemID(Scene, Item), NewEnabled)


    def SetFilterEnabled(self, Source, Filter, NewEnabled):
        Response = self.SendRequest("SetSourceFilterEnabled", "SetFilterEnabled", {
            "sourceName" : Source,
            "filterName" : Filter,
            "filterEnabled" : NewEnabled
        })

        #print(Response)








