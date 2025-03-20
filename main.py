import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication
import signal
import os
import threading
from SerialDeviceSanner import DevicePortScanner
from BaseStation import BaseController
from BaseTCPServer import BaseTCPServer
import Console
import VariableManager

current_path = os.path.dirname(os.path.abspath(__file__))

os.environ["QT_QPA_PLATFORM"] = "offscreen"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    VariableManager.instance.load("global_variable.ini")
    # TCP server
    tcp_server = BaseTCPServer()
    tcp_server.start()

    # Scan gps port
    scanner = DevicePortScanner()
    scanner_thread = QThread()
    scanner.moveToThread(scanner_thread)
    scanner_thread.start()
    gps_port = scanner.find_base_port()
    
    cmd = Console.ExternalCmdServer()
    threadSocketIO = threading.Thread(target=Console.socketio_thread)
    threadSocketIO.daemon = True
    threadSocketIO.start()
    
    # Base Station
    base_station = BaseController(port=gps_port)
    base_station_thread = QThread()
    base_station.moveToThread(base_station_thread)
    base_station_thread.started.connect(base_station.run_fixed_mode)
    base_station_thread.start()
    
    
    cmd.survey_in.connect(base_station.start_survey_in_mode)
    cmd.fixed.connect(base_station.start_fixed_mode)
    cmd.rate.connect(base_station.set_rate)
    cmd.request_signal.connect(base_station.get_data)
    base_station.rtcm3_signal.connect(tcp_server.send_RTCM3,Qt.ConnectionType.QueuedConnection)
    base_station.survey_in_data.connect(cmd.send_svin_status)
    base_station.base_data.connect(cmd.respone_data)
    app.aboutToQuit.connect(tcp_server.stop)
    
    base_station.get_data() # emit to nest server
    
    timer = QTimer()
    timer.start(100)  # mỗi 100ms
    timer.timeout.connect(lambda: None)

    def handleIntSignal(signum, frame):
        tcp_server.stop()
        scanner_thread.quit()
        scanner_thread.wait(2000)
        base_station_thread.quit()
        base_station_thread.wait(2000)
        app.quit()

    signal.signal(signal.SIGINT, handleIntSignal)

    sys.exit(app.exec())
