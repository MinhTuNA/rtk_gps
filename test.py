import serial
import socket
import threading

# Cấu hình cổng Serial để nhận tín hiệu RTCM3
SERIAL_PORT = "/dev/ttyUSB0"  # Thay đổi theo thiết bị của bạn
BAUD_RATE = 115200

# Cấu hình TCP server
TCP_HOST = "0.0.0.0"  # Lắng nghe tất cả địa chỉ
TCP_PORT = 2101  # Port của TCP server

def handle_client(client_socket):
    """ Xử lý dữ liệu từ client """
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"Received from client: {data.hex()}")
    except Exception as e:
        print(f"Client disconnected: {e}")
    finally:
        client_socket.close()

def tcp_server():
    """ Khởi chạy TCP server """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((TCP_HOST, TCP_PORT))
    server.listen(5)
    print(f"TCP server is listening on {TCP_HOST}:{TCP_PORT}")

    while True:
        client_socket, addr = server.accept()
        print(f"New connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

def serial_to_tcp():
    """ Nhận dữ liệu từ Serial và gửi lên TCP server """
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Listening on Serial {SERIAL_PORT} at {BAUD_RATE} baud")
        
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect(("127.0.0.1", TCP_PORT))  # Kết nối đến TCP server cục bộ

        while True:
            data = ser.read(1024)  # Đọc dữ liệu từ cổng Serial
            if data:
                print(f"Sending RTCM3 data to TCP server: {data.hex()}")
                tcp_socket.sendall(data)  # Gửi lên TCP server

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ser.close()
        tcp_socket.close()

if __name__ == "__main__":
    # Chạy TCP server trong một luồng riêng biệt
    server_thread = threading.Thread(target=tcp_server, daemon=True)
    server_thread.start()

    # Chạy chương trình đọc từ Serial và gửi lên TCP
    serial_to_tcp()
