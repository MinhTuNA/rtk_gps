import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication
import signal
import os

from BaseStation import BaseController
from ConstVariable import BASE_STATION
from BaseTCPServer import BaseTCPServer

os.environ["QT_QPA_PLATFORM"] = "offscreen"

if __name__ == "__main__":
    app = QApplication(sys.argv)

    tcp_server = BaseTCPServer()
    tcp_server_thread = QThread()
    tcp_server.moveToThread(tcp_server_thread)
    tcp_server_thread.started.connect(tcp_server.run)
    tcp_server_thread.start()

    def handleIntSignal(signum, frame):
        tcp_server.stop()
        tcp_server_thread.quit()
        tcp_server_thread.wait()
        app.quit()

    signal.signal(signal.SIGINT, handleIntSignal)

    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Không làm gì, chỉ để tránh block
    timer.start(100)

    sys.exit(app.exec())
