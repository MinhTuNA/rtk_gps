import socket
import serial
import threading
import time
import signal
from um982lib import GPSDevice
TCP_SERVER_IP = "192.168.1.230"
TCP_SERVER_PORT = 9876

SERIAL_PORT = "COM9"
BAUD_RATE = 115200

stop_event = threading.Event()


class UM982():
    def __init__(self):
        self.serial_port = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        self.gps_device = GPSDevice()

    def receive_rtcm_and_send_to_serial(self):
        try:
            tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_client.connect((TCP_SERVER_IP, TCP_SERVER_PORT))
            print(
                f"[INFO] Connected to RTCM Server {TCP_SERVER_IP}:{TCP_SERVER_PORT}")

            while not stop_event.is_set():
                data = tcp_client.recv(1024)
                if not data:
                    print("[INFO] No more RTCM data. Closing connection.")
                    break  # Dừng nếu mất kết nối
                self.serial_port.write(data)  # Gửi RTCM vào COM9
                # print(f"[RTCM] Sent {len(data)} bytes to {SERIAL_PORT}")

        except Exception as e:
            print(f"[ERROR] RTCM Transfer Error: {e}")

        finally:
            tcp_client.close()

    def read_gps(self):
        try:
            print(
                f"[INFO] Reading GPS data from {SERIAL_PORT} at {BAUD_RATE} baud")

            while not stop_event.is_set():
                gps_data = self.serial_port.readline().decode(errors='ignore').strip()
                if gps_data:
                    gps_data_parsed = self.gps_device.parse_um982_data(
                        gps_data
                    )
                    if gps_data_parsed is None:
                        continue
                    # print(f"gps >> {gps_data_parsed}")
                    if gps_data_parsed["type"] == "rtk_status_msg":
                        pass
                    if gps_data_parsed["type"] == "uniheading_msg":
                        heading = gps_data_parsed["heading"]
                        print(f"heading >> {heading}")
                    if gps_data_parsed["type"] == "adrnav_msg":
                        pos_type = gps_data_parsed["pos_type"]
                        lat = gps_data_parsed["lat"]
                        lon = gps_data_parsed["lon"]
                        print(
                            f"pos type: {pos_type} \n"
                            f"lat >> {lat} \n"
                            f"lon >> {lon} \n"
                        )
                    if gps_data_parsed["type"] == "rtcm_status_msg":
                        msg_id = gps_data_parsed["msg_id"]
                        print(f"RTCM {msg_id}")

        except Exception as e:
            print(f"[ERROR] GPS Read Error: {e}")


def handle_exit(signum, frame):
    print("\n[INFO] Ctrl + C detected! Stopping program...")

    # Dừng tất cả các vòng lặp trong các thread
    stop_event.set()

    # Chờ các thread dừng lại
    rtcm_thread.join()
    gps_thread.join()

    # Đóng Serial Port
    if um982.serial_port:
        um982.serial_port.close()
        print(f"[INFO] Closed Serial Port {SERIAL_PORT}")

    print("[INFO] Program exited safely. Goodbye!")
    exit(0)


# Chạy hai tiến trình song song:
if __name__ == "__main__":
    # Bắt tín hiệu Ctrl + C
    signal.signal(signal.SIGINT, handle_exit)

    um982 = UM982()

    # Chạy hai tiến trình song song
    rtcm_thread = threading.Thread(
        target=um982.receive_rtcm_and_send_to_serial)
    gps_thread = threading.Thread(target=um982.read_gps)

    rtcm_thread.start()
    gps_thread.start()

    # Giữ chương trình chạy
    while not stop_event.is_set():
        time.sleep(1)
