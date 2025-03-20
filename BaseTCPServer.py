from PySide6.QtCore import QThread, Signal as pyqtSignal, QObject, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QTcpServer, QTcpSocket, QHostAddress
from ConstVariable import BASE_STATION
import sys
import serial
import socket
import threading
import time
import signal
import VariableManager


class BaseTCPServer(QObject):
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.TCP_HOST = None
        self.TCP_PORT = None
        self.server = QTcpServer(self)
        self.clients = set()
        self.running = True
        self.load_setting()
        
        self.server.newConnection.connect(self.handle_new_connection)
    
    def start(self):
        if not self.server.listen(QHostAddress(self.TCP_HOST), self.TCP_PORT):
            self.error_signal.emit(f"Server failed to start: {self.server.errorString()}")
        else:
            print(f"[SERVER STARTED] Listening on {self.TCP_HOST}:{self.TCP_PORT}")

    def load_setting(self):
        self.TCP_HOST = VariableManager.instance.get("tcp.host", "0.0.0.0")
        self.TCP_PORT = int(VariableManager.instance.get("tcp.port", 8765))
    
    def handle_new_connection(self):
        while self.server.hasPendingConnections():
            client_socket = self.server.nextPendingConnection()
            client_socket.disconnected.connect(lambda sock=client_socket: self.remove_client(sock))
            client_socket.readyRead.connect(lambda sock=client_socket: self.read_data(sock))
            self.clients.add(client_socket)

            address = client_socket.peerAddress().toString()
            port = client_socket.peerPort()
            print(f"[NEW CONNECTION] {address}:{port} connected")

    def read_data(self, client_socket: QTcpSocket):
        data = client_socket.readAll()
        print(f"[DATA RECEIVED] {data.data()}")

    def remove_client(self, client_socket: QTcpSocket):
        address = client_socket.peerAddress().toString()
        port = client_socket.peerPort()
        print(f"[DISCONNECTED] {address}:{port}")

        client_socket.deleteLater()
        self.clients.discard(client_socket)

    def send_RTCM3(self, data: bytes):
        """Gửi RTCM3 tới tất cả client đang kết nối"""
        if not self.clients:
            return
        
        remove_clients = []
        for client in self.clients:
            if client.state() != QTcpSocket.ConnectedState:
                remove_clients.append(client)
                continue

            try:
                client.write(data)
            except Exception as e:
                print(f"[ERROR] Failed to send data to client: {e}")
                remove_clients.append(client)

        for client in remove_clients:
            self.clients.discard(client)

    def stop(self):
        """Dừng server"""
        print("[SERVER STOPPING]")
        self.server.close()
        self._close_all_clients()

    def _close_all_clients(self):
        while self.clients:
            client = self.clients.pop()
            client.close()
        self.clients.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    tcp_server = BaseTCPServer()
    tcp_server.start()  # Dùng .start() thay vì moveToThread()

    app.aboutToQuit.connect(tcp_server.stop)

    timer = QTimer()
    timer.start(100)  # mỗi 100ms
    timer.timeout.connect(lambda: None)

    # Đảm bảo server dừng đúng khi thoát
    def cleanup():
        print("[INFO] Stopping TCP Server...")
        tcp_server.stop()

    def handleIntSignal(signum, frame):
        print("Interrupt signal close app")
        cleanup()
        app.quit()

    signal.signal(signal.SIGINT, handleIntSignal)

    sys.exit(app.exec())
