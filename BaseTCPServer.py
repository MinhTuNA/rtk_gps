from PySide6.QtCore import QThread, Signal
from ConstVariable import BASE_STATION
import serial
import socket
import threading
import time

class BaseTCPServer(QThread):
    def __init__(self):
        self.TCP_HOST = BASE_STATION.tcp_host
        self.TCP_PORT = BASE_STATION.tcp_port
        self.clients = []
        self.lock = threading.Lock()

    def handle_client(self,client_socket, address):
        self.clients
        print(f"[NEW CONNECTION] {address} connected.")

        with self.lock:
            self.clients.append(client_socket)  # Thêm client vào danh sách

        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
        except:
            pass
        finally:
            with self.lock:
                self.clients.remove(client_socket)  # Xóa client khi ngắt kết nối
            client_socket.close()
            print(f"[DISCONNECTED] {address} disconnected.")


    def run_tcp_server(self):
        """ Chạy TCP server để phát dữ liệu RTCM3 """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.TCP_HOST, self.TCP_PORT))
        server.listen(5)
        print(f"[SERVER STARTED] Listening on {self.TCP_HOST}:{self.TCP_PORT}")

        while True:
            client_socket, addr = server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            client_thread.start()

    def send_RTCM3(self,data):
        """ Gửi tới tất cả client đang kết nối """
        try:
            rtcm_data = data
            with self.lock:
                for client in self.clients:
                    try:
                        client.sendall(rtcm_data)  # Gửi dữ liệu RTCM3 đến tất cả client
                    except:
                        self.clients.remove(client)
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            pass

if __name__ == "__main__":
    # Chạy TCP server trong một luồng riêng biệt
    tcp_server = BaseTCPServer()
    server_thread = threading.Thread(target=tcp_server.run_tcp_server, daemon=True)
    server_thread.start()
    while True:
        time.sleep(1)

    
