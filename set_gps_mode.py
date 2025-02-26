import serial
import time

uart_port = "COM7"
baudrate = 115200


def set_survey_in_mode():

    ser = serial.Serial(uart_port, baudrate, timeout=1)

    hex_strings = [
        "B5 62 06 8A 19 00 01 05 00 00 01 00 03 20 01 10 00 03 40 3C 00 00 00 11 00 03 40 C8 00 00 00 7F CD",
        "B5 62 06 8A 09 00 01 01 00 00 8B 00 91 20 01 D8 E5",
        "B5 62 06 8A 09 00 01 04 00 00 8B 00 91 20 01 DB FD"
    ]

    for hex_str in hex_strings:
        data = bytes.fromhex(hex_str)
        ser.write(data)
        print("Đã gửi dữ liệu:", data)
        time.sleep(1)

    ser.close()


def disable_mode():

    ser = serial.Serial(uart_port, baudrate, timeout=1)

    hex_strings = [
        "B5 62 06 8A 09 00 01 05 00 00 01 00 03 20 00 C3 A8",
    ]

    for hex_str in hex_strings:
        data = bytes.fromhex(hex_str)
        ser.write(data)
        print("Đã gửi dữ liệu:", data)

        time.sleep(1)
    ser.close()


if __name__ == "__main__":
    # set_survey_in_mode()
    disable_mode()
