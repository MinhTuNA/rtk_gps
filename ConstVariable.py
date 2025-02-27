
class IMU:
    baudrate = 460800
    serial_number = "5919000639"
    uart_buf_len = 512
    cnt_per_seconds = 1000


class GPS:
    baudrate = 115200
    serial_number = "DU0D6VH3"


class ULTRASONIC:
    baudrate = 115200
    serial_number = "5761037141"
    min_range = 0.03  # m
    max_range = 4.5  # m


class RS485:
    baudrate = 9600
    serial_number = "B003LK5S"
    read_mode = 0x03
    write_mode = 0x10


class BASE_STATION:
    baudrate = 115200
    serial_number = None
    Description = "u-blox GNSS receiver"
