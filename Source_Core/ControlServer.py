import socket
import threading
import queue
from Source_Core.Types import ChatMessage, DataMessage
from Source_Core.CommunicationBus import CoreComponent_BusConnected

class ControlServer(CoreComponent_BusConnected):

    def __init__(self, InCore, InAdress):
        super().__init__(InCore, InAdress, "Init Control Server")

        self.Host = "127.0.0.1"
        self.Port = 22222

        self.ControlSocket = None

        self.ConnectionThread = threading.Thread(target=AsyncServerLoop, args=(self,), daemon=True)
        self.ConnectionThread.start()

        self.TaskQueue = queue.Queue()


    def UpdateControlServer(self):

        while not self.TaskQueue.empty():
            Task = self.TaskQueue.get()

            Message = str(Task)[2:-1].replace('\\n', '')
            CMsg = ChatMessage("CONTROL SERVER", "-", "CONTROL SERVER", Message)
            InstructionCallMessage = DataMessage("Instructions", self.Address, "IN", {"Head" : "COMMAND_ProcessMessageCommands", "Data" : {"Message" : CMsg, "WasFiltered" : False}})
            self.TransmitData(InstructionCallMessage)


    def ParseTaskMessage(self, InTaskMessage):
        return True, InTaskMessage


def AsyncServerLoop(InControlServer):
    CS = InControlServer

    while True:
        try:

            CS.ControlSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            CS.ControlSocket.bind((CS.Host, CS.Port))
            CS.ControlSocket.listen()

            Connect, Address = CS.ControlSocket.accept()

            with Connect:
                CS.LLogger.LogStatus(f"CONTROL SERVER: Connected by {Address}")

                while True:
                    Data = Connect.recv(1024)
                    CS.LLogger.LogStatus(f"CONTROL SERVER: Received: '{str(Data)}' from {Address}")

                    if not Data:
                        CS.LLogger.LogStatus(f"CONTROL SERVER: Connection Closed by {Address}")
                        break

                    ValidTask, Task = CS.ParseTaskMessage(Data)

                    if ValidTask:
                        CS.TaskQueue.put(Task)
                        Connect.sendall(b"Command Processed")

                    else:
                        Connect.sendall(b"Invalid Command!")

        except Exception as e:
            CS.LLogger.LogError("CONTROL SEVER: " + str(e))



