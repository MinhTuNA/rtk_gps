import serial
import struct
import sys


def calculate_checksum(data):
    """
    Tính checksum UBX trên dữ liệu truyền vào.
    CK_A = (sum các byte) mod 256
    CK_B = (tích lũy CK_A) mod 256
    """
    ck_a = 0
    ck_b = 0
    for b in data:
        ck_a = (ck_a + b) & 0xFF
        ck_b = (ck_b + ck_a) & 0xFF
    return ck_a, ck_b


def parse_ubx_message(buffer):
    """
    Tìm kiếm và tách một khung tin UBX từ buffer.
    Trả về tuple (msg_class, msg_id, payload) nếu tìm thấy message hợp lệ,
    và buffer đã được cắt bỏ phần message đã xử lý.

    buffer là một bytearray.
    """
    header_index = buffer.find(b'\xB5\x62')
    if header_index == -1:
        return None, bytearray()
    if header_index > 0:
        buffer = buffer[header_index:]

    if len(buffer) < 6:
        return None, buffer

    msg_class = buffer[2]
    msg_id = buffer[3]
    length = buffer[4] | (buffer[5] << 8)  # Đọc độ dài payload (little-endian)

    total_length = 6 + length + 2
    if len(buffer) < total_length:
        return None, buffer

    message = buffer[:total_length]
    ck_a, ck_b = calculate_checksum(message[2:6+length])
    if ck_a != message[-2] or ck_b != message[-1]:
        print("Checksum không hợp lệ!")
        return None, buffer[1:]

    payload = message[6:6+length]
    buffer = buffer[total_length:]
    return (msg_class, msg_id, payload), buffer


def decode_ubx_svin(payload):
    """
    Giải mã payload UBX-NAV-SVIN (40 byte) và trả về dictionary chứa các trường:
      - version, reserved0, iTOW, dur, meanX, meanY, meanZ,
        meanXHP, meanYHP, meanZHP, reserved1, meanAcc, obs, valid, active, reserved2
      - x_mm, y_mm, z_mm: tọa độ sau khi kết hợp phần nguyên và phần thập phân.

    Cấu trúc theo tài liệu UBX-NAV-SVIN:
      • B    : version     (1 byte, unsigned)
      • 3s   : reserved0   (3 byte, unsigned)
      • I    : iTOW        (4 byte, unsigned)
      • i    : dur         (4 byte, signed)
      • i    : meanX       (4 byte, signed)
      • i    : meanY       (4 byte, signed)
      • i    : meanZ       (4 byte, signed)
      • b    : meanXHP     (1 byte, signed)
      • b    : meanYHP     (1 byte, signed)
      • b    : meanZHP     (1 byte, signed)
      • B    : reserved1   (1 byte, unsigned)
      • I    : meanAcc     (4 byte, unsigned)
      • I    : obs         (4 byte, unsigned)
      • B    : valid       (1 byte, unsigned)
      • B    : active      (1 byte, unsigned)
      • H    : reserved2   (2 byte, unsigned)
    """
    if len(payload) != 40:
        raise ValueError(
            f"Payload UBX-NAV-SVIN phải có độ dài 40 byte, nhận được {len(payload)} byte")

    fmt = "<B3sIiiiibbbBIIBBH"
    fields = struct.unpack(fmt, payload)
    (version, reserved0, iTOW, dur, meanX, meanY, meanZ,
     meanXHP, meanYHP, meanZHP, reserved1, meanAcc, obs, valid, active, reserved2) = fields

    # Tính tọa độ: meanX, meanY, meanZ được tính theo cm -> chuyển ra mm (nhân 10)
    # meanXHP, meanYHP, meanZHP tính theo 0.1 mm -> chia 10
    # x_mm = meanX * 10 + meanXHP / 10.0
    # y_mm = meanY * 10 + meanYHP / 10.0
    # z_mm = meanZ * 10 + meanZHP / 10.0

    if (active == 1):
        print("Survey-In chua hoan tat")
    else:
        print("Survey-In hoan tat")
        with open("survey_in_complete.txt", "a") as f:
            f.write(f"Version: {version}\n")
            f.write(f"iTOW: {iTOW}\n")
            f.write(f"Duration: {dur}\n")
            f.write(f"Mean X: {meanX}\n")
            f.write(f"Mean Y: {meanY}\n")
            f.write(f"Mean Z: {meanZ}\n")
            f.write(f"Mean X HP: {meanXHP}\n")
            f.write(f"Mean Y HP: {meanYHP}\n")
            f.write(f"Mean Z HP: {meanZHP}\n")
            f.write(f"Mean Accuracy: {meanAcc}\n")
            f.write(f"Observations: {obs}\n")
            f.write(f"Valid: {valid}\n")
            f.write(f"Active: {active}\n")
            f.write("\n")

        sys.exit()

    return {
        "version": version,
        "reserved0": reserved0,
        "iTOW": iTOW,
        "dur": dur,
        "meanX": meanX,         # cm
        "meanY": meanY,         # cm
        "meanZ": meanZ,         # cm
        "meanXHP": meanXHP,     # 0.1 mm
        "meanYHP": meanYHP,     # 0.1 mm
        "meanZHP": meanZHP,     # 0.1 mm
        "reserved1": reserved1,
        "meanAcc": meanAcc,    # độ chính xác trung bình (0.1 mm)
        "obs": obs,
        "valid": valid,
        "active": active,
        "reserved2": reserved2,
        # "x_mm": x_mm,
        # "y_mm": y_mm,
        # "z_mm": z_mm
    }


def main():
    # Thay đổi port và baudrate theo cấu hình thực tế của bạn.
    port = "COM7"  # Ví dụ: trên Windows, có thể là "COM3"; trên Linux: "/dev/ttyUSB0"
    baudrate = 115200

    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Đã mở cổng {port} với baudrate {baudrate}")
    except Exception as e:
        print(f"Lỗi mở cổng: {e}")
        return

    buffer = bytearray()

    try:
        while True:
            # Đọc dữ liệu từ UART (tối đa 1024 byte mỗi lần)
            data = ser.read(1024)
            if data:
                buffer.extend(data)
                # Xử lý buffer: liên tục tìm kiếm các khung tin UBX hợp lệ
                while True:
                    result, buffer = parse_ubx_message(buffer)
                    if result is None:
                        break
                    msg_class, msg_id, payload = result
                    # Kiểm tra nếu là UBX-NAV-SVIN (class 0x01, id 0x3B)
                    if msg_class == 0x01 and msg_id == 0x3B:
                        try:
                            svin_data = decode_ubx_svin(payload)
                        except Exception as e:
                            print("Lỗi khi giải mã UBX-NAV-SVIN:", e)
                        else:
                            print("Dữ liệu UBX-NAV-SVIN nhận được:")
                            with open("svin_data.txt", "a") as f:
                                for key, value in svin_data.items():
                                    line = f"{key}: {value}"
                                    print("  " + line)
                                    f.write(line + "\n")
                                f.write("\n")
    except KeyboardInterrupt:
        print("Ngắt chương trình.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
