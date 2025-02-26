import smbus
import time
import math

IST8310_ADDR = 0x0E

DATA_X_LSB = 0x03
DATA_X_MSB = 0x04
DATA_Y_LSB = 0x05
DATA_Y_MSB = 0x06
DATA_Z_LSB = 0x07
DATA_Z_MSB = 0x08

CTRL1 = 0x0A
RESET = 0x0B

bus = smbus.SMBus(1)

def initialize_ist8310():
    try:
        bus.write_byte_data(IST8310_ADDR, CTRL1, 0x0B)
        time.sleep(0.1)

        who_am_i = bus.read_byte_data(IST8310_ADDR, 0x00)
        if who_am_i != 0x10:
            print("IST8310 not found !")
            return False

        print("IST8310 is ready.")
        return True
    except Exception as e:
        print(f"unknown error: {e}")
        return False

def reset_ist8310():
    bus.write_byte_data(IST8310_ADDR, RESET, 0x01)
    time.sleep(0.1)
    print("IST8310 has been reset.")

def read_axis(lsb_reg, msb_reg):
    try:
        lsb = bus.read_byte_data(IST8310_ADDR, lsb_reg)
        msb = bus.read_byte_data(IST8310_ADDR, msb_reg)
        value = (msb << 8) | lsb
        if value >= 32768:
            value -= 65536
        return value
    except Exception as e:
        print(f"error when reading {lsb_reg}-{msb_reg}: {e}")
        return 0

def calculate_heading(x, y):
    RAD_TO_DEG = 180 / math.pi

    if x > 0:
        degrees = 90 - math.atan2(y, x) * RAD_TO_DEG
    elif x == 0 and y > 0:
        degrees = (math.pi / 2) * RAD_TO_DEG
    elif x == 0 and y < 0:
        degrees = (-math.pi / 2) * RAD_TO_DEG
    elif x < 0 and y >= 0:
        degrees = 90 - (math.atan2(y, x)) * RAD_TO_DEG
    elif x < 0 and y < 0:
        degrees = -90 - (math.atan2(y, x) + math.pi) * RAD_TO_DEG

    degrees = -degrees
    degrees = degrees % 360
    return degrees

def get_direction(heading):
    if 337.5 <= heading < 360 or 0 <= heading < 22.5:
        return "N"
    elif 22.5 <= heading < 67.5:
        return "NE"
    elif 67.5 <= heading < 112.5:
        return "E"
    elif 112.5 <= heading < 157.5:
        return "SE"
    elif 157.5 <= heading < 202.5:
        return "S"
    elif 202.5 <= heading < 247.5:
        return "SW"
    elif 247.5 <= heading < 292.5:
        return "W"
    elif 292.5 <= heading < 337.5:
        return "NW"
    return "Không xác định"

def get_ist8310_data():
    try:
        x = read_axis(DATA_X_LSB, DATA_X_MSB)
        y = read_axis(DATA_Y_LSB, DATA_Y_MSB)
        z = read_axis(DATA_Z_LSB, DATA_Z_MSB)
        heading = calculate_heading(x, y)
        direction = get_direction(heading)
        return {
            "x": x,
            "y": y,
            "z": z,
            "heading": heading,
            "direction": direction
        }
    except Exception as e:
        print(f"Lỗi khi đọc dữ liệu cảm biến: {e}")
        return None
    
if __name__ == "__main__":
    try:
        reset_ist8310()
        if not initialize_ist8310():
            exit()

        print("Đang đọc dữ liệu từ cảm biến IST8310...")
        while True:
            data = get_ist8310_data()
            if data:
                print(f"X: {data['x']}, Y: {data['y']}, Z: {data['z']}, "
                      f"Hướng: {data['direction']} ({data['heading']:.2f}°)")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Dừng chương trình.")