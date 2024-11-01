import websocket
import base64
import hashlib
import json

from Source.Types import ObsAuthData

class ObsInterface:
    def __init__(self, InConfigController):

        self.LConfigController = InConfigController
        self.AuthData = ObsAuthData(
            "localhost",
            4455,
            "hehe"
        )

        url = "ws://{}:{}".format(self.AuthData.host, self.AuthData.port)
        self.ObsWS = websocket.WebSocket()
        self.ObsWS.connect(url)


    def GenerateAuthString(self, Challenge, Salt):

        Base64Secret = base64.b64encode(hashlib.sha256((self.AuthData.password + Salt).encode("utf-8")).digest())
        Auth = base64.b64encode(hashlib.sha256(Base64Secret + Challenge.encode("utf-8")).digest()).decode("utf-8")

        return Auth

    def Authenticate(self):

        HelloMsg = self.ObsWS.recv()
        Res = json.loads(HelloMsg)
        Auth = self.GenerateAuthString(Res['d']["authentication"]["challenge"], Res['d']["authentication"]["salt"])

        Payload = {
              "op": 1,
              "d": {
                "rpcVersion": 1,
                "authentication": Auth,
                "eventSubscriptions": 1000
              }
            }




