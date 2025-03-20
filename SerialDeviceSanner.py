import sys
import glob
import serial
import time
import serial.tools
import serial.tools.list_ports
from ConstVariable import *
import os
import sys
from PySide6.QtCore import Signal as pyqtSignal, QObject


class DevicePortScanner(QObject):

    def __init__(self):
        super().__init__()
        self.hand_camera_order = None
        self.calib_camera_order = None

        self.rs485_serial_number = RS485.serial_number
        self.um982_serial_number = GPS.serial_number
        self.imu_serial_number = IMU.serial_number
        self.ultrasonic_serial_number = ULTRASONIC.serial_number
        self.base_serial_number = BASE_STATION.serial_number
        self.base_description = BASE_STATION.description
        self.ports = self.list_serial_ports()

    def refresh(self):
        self.ports = self.list_serial_ports()

        # kiểm tra xem có cổng nào là của DeltaX không
        delta_x_port = self.find_delta_x_port()
        if delta_x_port is not None:
            pass

        # kiểm tra xem có cổng nào là của Encoder X không
        encoder_x_port = self.find_encoder_x_port()

    def list_serial_ports(self):

        ports = serial.tools.list_ports.comports()
        # result = []
        # for port in ports:
        #     print(f"Device: {port.device}")
        #     print(f"Name: {port.name}")
        #     print(f"Description: {port.description}")
        #     print(f"Manufacturer: {port.manufacturer}")
        #     print(f"Serial Number: {port.serial_number}")
        #     print(f"Location: {port.location}")
        #     print(f"Vendor ID: {port.vid if port.vid else 'Unknown'}")
        #     print(f"Product ID: {port.pid if port.pid else 'Unknown'}")
        #     print("-" * 40)
        # try:
        #     s = serial.Serial(port)
        #     s.close()
        #     result.append(port)
        # except (OSError, serial.SerialException):
        #     pass
        return ports

    def find_delta_x_port(self):
        for port in self.ports:
            try:
                ser = serial.Serial(port, baudrate=115200, timeout=1)
                ser.write(b"IsDelta\n")
                response = ser.readline().decode("utf-8").strip()
                ser.close()
                if response == "YesDelta":
                    return port
            except (OSError, serial.SerialException):
                pass
        return None

    def find_encoder_x_port(self):
        for port in self.ports:
            try:
                ser = serial.Serial(port, baudrate=115200, timeout=1)
                ser.write(b"IsXConveyor\n")
                response = ser.readline().decode("utf-8").strip()
                ser.close()
                if response == "YesXConveyor":
                    return port
            except (OSError, serial.SerialException):
                pass
        return None

    def find_rs485_port(self):
        for port in self.ports:
            if port.serial_number == self.rs485_serial_number:
                return port.device
        return None

    def find_imu_port(self):
        for port in self.ports:
            if port.serial_number == self.imu_serial_number:
                return port.device
        return None

    def find_um982_port(self):
        for port in self.ports:
            if port.serial_number == self.um982_serial_number:
                return str(port.device)
        return None

    def find_s21c_port(self):
        for port in self.ports:
            if port.serial_number == self.ultrasonic_serial_number:
                return port.device
        return None

    def find_base_port(self):
        for port in self.ports:
            if (
                port.description == self.base_description
                and port.serial_number == self.base_serial_number
            ):
                print(f"base port >> {port.device}")
                return port.device
        print(f"port not found")
        return None


if __name__ == "__main__":
    scanner = DevicePortScanner()
    print(f"rs485 >> {scanner.find_rs485_port()}")
    print(f"imu >> {scanner.find_imu_port()}")
    print(f"um982 >> {scanner.find_um982_port()}")
    print(f"s21c >> {scanner.find_s21c_port()}")
    print(f"base >> {scanner.find_base_port()}")
    # print("xencoder: ", scanner.find_encoder_x_port())
    # print("deltax", scanner.find_delta_x_port())
