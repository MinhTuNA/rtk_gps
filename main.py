import sys

from PySide6.QtCore import Qt
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication

import os

from BaseStation import BaseController
from ConstVariable import BASE_STATION
from BaseTCPServer import BaseTCPServer
import threading
import time

os.environ["QT_QPA_PLATFORM"] = "offscreen"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    tcp_server = BaseTCPServer()
    server_thread = threading.Thread(target=tcp_server.run_tcp_server, daemon=True)
    server_thread.start()
    while True:
        time.sleep(1)
    
    