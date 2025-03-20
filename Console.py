from PySide6.QtCore import QObject, Signal as pyqtSignal, QMutex, QTimer
from PySide6.QtWidgets import QApplication
import socketio
import time
import VariableManager
sio = socketio.Client()


class ExternalCmdServer(QObject):
    fixed = pyqtSignal(int, int, int, int)
    survey_in = pyqtSignal(int, int)
    disable = pyqtSignal()
    rate = pyqtSignal(int)
    request_signal = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.sio = sio
        self.is_connected = False

        self.hasRegisteredEvents = False
        if not self.hasRegisteredEvents:
            self.sio.on("connect", self.on_connect, namespace="/base")
            self.sio.on("fixed", self.handle_fixed, namespace="/base")
            self.sio.on("survey_in", self.handle_survey_in, namespace="/base")
            self.sio.on("rate", self.handle_rate, namespace="/base")
            self.sio.on("request_data",self.handle_request_data, namespace="/base")

    def on_connect(self):
        self.is_connected = True
        print("Connected to socketio")

    def handle_fixed(self, data):
        ecef_x = int(data["ecef_x"])
        ecef_y = int(data["ecef_y"])
        ecef_z = int(data["ecef_z"])
        acc = int(data["acc"])
        # print(f"x >> {ecef_x}")
        # print(f"y >> {ecef_y}")
        # print(f"z >> {ecef_z}")
        # print(f"acc >> {acc}")
        self.fixed.emit(ecef_x, ecef_y, ecef_z, acc)

    def handle_survey_in(self, data):
        dur = int(data["dur"])
        acc = int(data["acc"])
        # print(f"dur >> {dur}")
        # print(f"acc >> {acc}")
        self.survey_in.emit(dur, acc)
        # self.survey_in.emit()
    
    def handle_rate(self,rate):
        _rate = int(rate)
        self.rate.emit(_rate)
        
    def handle_request_data(self,data):
        self.request_signal.emit()
    
    def respone_data(self,data):
        base_data = data
        self.emitToServer("base_data",base_data)
    
    def emitToServer(self, event, data):
        if self.sio.sid is None:
            return
        if self.is_connected == False:
            return
        self.sio.emit(event, data, namespace="/base")

    def send_svin_status(self, data):
        self.emitToServer("svin_status", data=data)


def socketio_thread():
    while True:
        # Connect to the Socket.IO server
        try:
            sio.connect("http://localhost:8901", namespaces=["/base"])
            print(f"Connection established to server at {sio.eio}")
            sio.wait()
        except socketio.exceptions.ConnectionError as e:
            print(f"Connection failed: {e}")
            time.sleep(3)
