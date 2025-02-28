from PySide6.QtCore import QThread, Signal as pyqtSignal, QObject
from PySide6.QtWidgets import QApplication
from ConstVariable import BASE_STATION
import sys
import serial
import socket
import threading
import time
import signal


class BaseTCPServer(QThread):
    def __init__(self):
        super().__init__()
        self.TCP_HOST = BASE_STATION.tcp_host
        self.TCP_PORT = BASE_STATION.tcp_port
        self.clients = []
        self.lock = threading.Lock()
        self.running = True

    def handle_client(self, client_socket, address):
        self.clients
        print(f"[NEW CONNECTION] {address} connected.")

        with self.lock:
            self.clients.append(client_socket)

        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
        except Exception as e:
            print(f"[ERROR] Client {address} Error: {e}")
        finally:
            with self.lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
            client_socket.close()
            print(f"[DISCONNECTED] {address} disconnected.")

    def run(self):
        """Chạy server TCP"""
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.TCP_HOST, self.TCP_PORT))
            self.server.listen(5)
            print(
                f"[SERVER STARTED] Listening on {self.TCP_HOST}:{self.TCP_PORT}")

            while self.running:
                try:
                    client_socket, addr = self.server.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client, args=(client_socket, addr), daemon=True)
                    client_thread.start()
                except Exception as e:
                    if self.running:
                        self.error_signal.emit(f"TCP Error: {e}")
        except Exception as e:
            self.error_signal.emit(f"Server failed to start: {e}")
        finally:
            print("[SERVER STOPPED]")
            self.cleanup()

    def send_RTCM3(self, data):
        """ Gửi tới tất cả client đang kết nối """
        try:
            rtcm_data = data
            with self.lock:
                for client in self.clients:
                    try:
                        # Gửi dữ liệu RTCM3 đến tất cả client
                        client.sendall(rtcm_data)
                    except:
                        self.clients.remove(client)
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            pass

    def stop(self):
        """Dừng server"""
        self.running = False
        if hasattr(self, 'server'):
            self.server.close()
        with self.lock:
            for client in self.clients:
                client.close()
            self.clients.clear()
        self.quit()
        self.wait()

    def cleanup(self):
        """Đóng tất cả kết nối khi dừng"""
        with self.lock:
            for client in self.clients:
                client.close()
            self.clients.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    tcp_server = BaseTCPServer()
    tcp_server.start()  # Dùng .start() thay vì moveToThread()

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
