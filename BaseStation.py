import serial
from PySide6.QtCore import QThread, Signal as pyqtSignal, QObject
from PySide6.QtSerialPort import QSerialPort
from ConstVariable import BASE_STATION
import struct
import time

class BaseState:
    DISABLE = 0
    SURVEY_IN = 1
    FIXED = 2

class BaseController(QObject):
    rtcm3_signal = pyqtSignal(bytes)
    
    def __init__(self,port):
        super().__init__()
        self.port = port
        self.baudrate = BASE_STATION.baudrate
        self.gps_serial = None
        self.is_connected = False

        self.NAV_SVIN_CLASS = 0x01
        self.NAV_SVIN_ID = 0x3B
        self.MSG_OUT_NAV2_SVIN_KEY_ID = [0x23,0x05,0x91,0x20]
        self.SET = [0x00]
        self.RESET = [0x00]
        
        self.MSG_OUT_RTCM3_1005_USB_KEY_ID = [0xC0,0x02,0x91,0x20] #0x209102c0
        self.MSG_OUT_RTCM3_1074_USB_KEY_ID = [0x61,0x03,0x91,0x20] #0x20910361
        self.MSG_OUT_RTCM3_1084_USB_KEY_ID = [0x66,0x03,0x91,0x20] #0x20910366
        self.MSG_OUT_RTCM3_1124_USB_KEY_ID = [0x70,0x03,0x91,0x20] #0x20910370
        self.MSG_OUT_RTCM3_1230_USB_KEY_ID = [0x06,0x03,0x91,0x20] #0x20910306
        
        self.MSG_OUT_NMEA_GBS_USB_KEY_ID = [0xE0, 0x00, 0x91, 0x20]  # 0x209100e0
        self.MSG_OUT_NMEA_GLL_USB_KEY_ID = [0xCC, 0x00, 0x91, 0x20]  # 0x209100cc
        self.MSG_OUT_NMEA_GNS_USB_KEY_ID = [0xB8, 0x00, 0x91, 0x20]  # 0x209100b8
        self.MSG_OUT_NMEA_GSA_USB_KEY_ID = [0xC2, 0x00, 0x91, 0x20]  # 0x209100c2
        self.MSG_OUT_NMEA_GSV_USB_KEY_ID = [0xC7, 0x00, 0x91, 0x20]  # 0x209100c7
        self.MSG_OUT_NMEA_GST_USB_KEY_ID = [0xD6, 0x00, 0x91, 0x20]  # 0x209100d6
        self.MSG_OUT_NMEA_RMC_USB_KEY_ID = [0xAE, 0x00, 0x91, 0x20]  # 0x209100ae
        self.MSG_OUT_NMEA_VTG_USB_KEY_ID = [0xB3, 0x00, 0x91, 0x20]  # 0x209100b3
        self.MSG_OUT_NMEA_GGA_USB_KEY_ID = [0xBD, 0x00, 0x91, 0x20]  # 0x209100bd
        
        self.DISABLE = [0x00]
        self.MODE_DISABLED = [0x00]
        self.MODE_SURVEY_IN = [0x01]
        self.MODE_FIXED = [0x02]

        self.UBX_VAL_SET_HEADER = [0xB5, 0x62]
        self.UBX_VAL_SET_CLASS = 0x06
        self.UBX_ID = 0x8A

        self.KEY_ID_TMODE3 = [0x01, 0x00, 0x03, 0x20]
        self.KEY_ID_SVIN_MIN_DUR = [0x10, 0x00, 0x03, 0x40]
        self.KEY_ID_SVIN_ACC_LIMIT = [0x11, 0x00, 0x03, 0x40]

        self.LLH = [0x01]
        self.ECEF = [0x00]
        self.KEY_ID_POS_TYPE = [0x02, 0x00, 0x03, 0x20]
        self.KEY_ID_ECEF_X = [0x03, 0x00, 0x03, 0x40]
        self.KEY_ID_ECEF_Y = [0x04, 0x00, 0x03, 0x40]
        self.KEY_ID_ECEF_Z = [0x05, 0x00, 0x03, 0x40]

        self.KEY_ID_ECEF_X_HP = [0x06, 0x00, 0x03, 0x20]
        self.KEY_ID_ECEF_Y_HP = [0x07, 0x00, 0x03, 0x20]
        self.KEY_ID_ECEF_Z_HP = [0x08, 0x00, 0x03, 0x20]
        self.KEY_ID_FIXED_ACCURACY = [0x0F, 0x00, 0x03, 0x40]

        self.RAM = 0x01
        self.FLASH = 0x04
        self.exit_survey_signal = False
        self.is_survey_in_complete = False

    def run(self):
          self.gps_serial = QSerialPort(self.port_name)
          self.gps_serial.setBaudRate(QSerialPort.BaudRate.Baud115200)          
          self.gps_serial.readyRead.connect(self.handle_read_data)
          
          if not self.gps_serial.open(QSerialPort.OpenModeFlag.ReadWrite):
               # VariableManager.instance.set(self.device_name + "_state", False)
               print("Failed to open base station port")
               return
          else:
               # VariableManager.instance.set(self.device_name + "_state", True)
               print("- XEncoder opened")

    
    def connect(self):
        if self.port == None:
            self.is_connected = False
            return
        try:
            self.gps_serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1,
            )
            self.is_connected = True
            print("connect successfully")
        except:
            self.is_connected = False
            print("connect to base error")
    
    def reconnect(self):
        print(f"Reconnect ZED-F9P {self.port}")
        self.connect()
        
    def handle_read_data(self):
        gps_data = self.read_data()

    def send_cmd(self, cmd):
        self.gps_serial.write(cmd)
        print(" ".join(cmd.hex()[i:i+2].upper()
                       for i in range(0, len(cmd.hex()), 2)))

    def calculate_checksum(self, payload):
        ck_a = 0
        ck_b = 0
        for byte in payload:
            ck_a = (ck_a + byte) % 256
            ck_b = (ck_b + ck_a) % 256
        return [ck_a, ck_b]

    def build_ubx_cfg_valset(self, keys_values, layer_):
        length = sum(len(key) + len(value)
                     for key, value in keys_values) + 4
        length_bytes = [length & 0xFF, (length >> 8) & 0xFF]
        version = [0x01]  # Version 1
        layer = [layer_]
        reserved = [0x00, 0x00]

        # Payload UBX-CFG-VALSET
        payload = version + layer + reserved
        for key, value in keys_values:
            payload += key + value

        checksum = self.calculate_checksum(
            [self.UBX_VAL_SET_CLASS, self.UBX_ID] + length_bytes + payload)

        return bytes(self.UBX_VAL_SET_HEADER + [self.UBX_VAL_SET_CLASS, self.UBX_ID] + length_bytes + payload + checksum)

    def set_survey_in_mode(self, duration=300, accuracy_=100, layer_=0x01):
        """
        duration (s)
        accuracy (mm)
        """
        accuracy = int(accuracy_ * 10)
        keys_values = [
            (self.KEY_ID_TMODE3, self.MODE_SURVEY_IN),  # Enable Survey-In
            (
                self.KEY_ID_SVIN_MIN_DUR,
                list(duration.to_bytes(4, 'little', signed=False))
            ),
            (
                self.KEY_ID_SVIN_ACC_LIMIT,
                list(accuracy.to_bytes(4, 'little', signed=False))
            )
        ]
        ubx_message = self.build_ubx_cfg_valset(keys_values, layer_)
        self.send_cmd(ubx_message)
        print(f"Survey-In Mode: Duration={duration}s, Accuracy={accuracy_}mm")

    def set_fixed_mode(self, ecef_x_, ecef_y_,ecef_z_, accuracy_, layer_=0x01):
        """
        x,y,z (cm)
        accuracy (mm)
        """
        ecef_x = ecef_x_
        ecef_y = ecef_y_
        ecef_z = ecef_z_

        accuracy = int(accuracy_ * 10)
        keys_values = [
            (self.KEY_ID_TMODE3, self.MODE_FIXED),
            (
                self.KEY_ID_FIXED_ACCURACY,
                list(accuracy.to_bytes(4, 'little', signed=False))
            ),
            (
                self.KEY_ID_POS_TYPE,
                self.ECEF
            ),
            (
                self.KEY_ID_ECEF_X,
                list(ecef_x.to_bytes(4, 'little', signed=True))
            ),
            (
                self.KEY_ID_ECEF_X_HP,
                self.DISABLE
            ),
            (
                self.KEY_ID_ECEF_Y,
                list(ecef_y.to_bytes(4, 'little', signed=True))
            ),
            (
                self.KEY_ID_ECEF_Y_HP,
                self.DISABLE
            ),
            (
                self.KEY_ID_ECEF_Z,
                list(ecef_z.to_bytes(4, 'little', signed=True))
            ),
            (
                self.KEY_ID_ECEF_Z_HP,
                self.DISABLE
            )
        ]
        ubx_message = self.build_ubx_cfg_valset(keys_values, layer_)
        self.send_cmd(ubx_message)
        print(
            f"Fixed Mode: X={ecef_x_}cm, Y={ecef_y_}cm, Z={ecef_z_}cm, Accuracy={accuracy_}mm")

    def _disable(self):
        cmd = [
            0xB5, 0x62 ,0x06 ,0x8A ,0x09 ,0x00 ,0x01 ,0x05 ,0x00 ,0x00 ,0x01 ,0x00 ,0x03 ,0x20 ,0x00 ,0xC3 ,0xA8
        ]
        _cmd = bytes(cmd)
        self.send_cmd(_cmd)
    
    def disable_NMEA(self):
        NMEA_ID_GGA_USB = [0xBD,0x00,0x91,0x20] #0x209100bd
        
        # keys_values = [
        #     self.
        # ]

    def svin_message(self,value,layer_):
        if value == 1:
            keys_values = [
                (self.MSG_OUT_NAV2_SVIN_KEY_ID, self.SET),  # Enable Survey-in MSG
            ]
        else :
            keys_values = [
                (self.MSG_OUT_NAV2_SVIN_KEY_ID, self.RESET),  # disable Survey-in MSG
            ]
        ubx_message = self.build_ubx_cfg_valset(keys_values, layer_)
        self.send_cmd(ubx_message)
    
    def enable_RTCM_message(self,layer_):
        keys_values = [
            (self.MSG_OUT_RTCM3_1005_USB_KEY_ID, self.SET),
            (self.MSG_OUT_RTCM3_1074_USB_KEY_ID, self.SET), 
            (self.MSG_OUT_RTCM3_1084_USB_KEY_ID, self.SET), 
            (self.MSG_OUT_RTCM3_1124_USB_KEY_ID, self.SET), 
            (self.MSG_OUT_RTCM3_1230_USB_KEY_ID, self.SET), # Enable Survey-in MSG
        ]
        ubx_message = self.build_ubx_cfg_valset(keys_values, layer_)
        self.send_cmd(ubx_message)
    
    def read_data(self):
        gps_data = self.gps_serial.read(1024)
        if gps_data is None:
            return None
        return gps_data

    def parse_ubx_message(self, buffer):
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
        # Đọc độ dài payload (little-endian)
        length = buffer[4] | (buffer[5] << 8)

        total_length = 6 + length + 2
        if len(buffer) < total_length:
            return None, buffer

        message = buffer[:total_length]
        ck_a, ck_b = self.calculate_checksum(message[2:6+length])
        if ck_a != message[-2] or ck_b != message[-1]:
            print("Checksum không hợp lệ!")
            return None, buffer[1:]

        payload = message[6:6+length]
        buffer = buffer[total_length:]
        return (msg_class, msg_id, payload), buffer

    def decode_ubx_svin(self, payload):
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

        data_decoded = {
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
        }

        if (valid == 1):
            self.is_survey_in_complete = True
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
                return data_decoded
        self.is_survey_in_complete = False
        return data_decoded

    def start_survey_in_mode(self,duration = 300, accuracy_=20):
        self._disable()
        self.set_survey_in_mode(duration=duration, accuracy_=accuracy_,layer_=self.RAM+self.FLASH)
        if self.is_connected == False:
            self.exit_survey_signal = True
            return
        buffer = bytearray()
        while self.exit_survey_signal == False | self.is_survey_in_complete == False:
            try:
                base_station_data = self.read_data()
                if base_station_data is None:
                    continue
                buffer.extend(base_station_data)
                result, buffer = self.parse_ubx_message(buffer=buffer)
                if result is None:
                    continue
                msg_class, msg_id, payload = result
                if msg_class == self.NAV_SVIN_CLASS and msg_id == self.NAV_SVIN_ID:
                    try:
                        svin_data = self.decode_ubx_svin(payload=payload)
                    except Exception as e:
                        print("lỗi giải mã :", e)
                    else:
                        with open("svin_data.txt", "a") as file:
                            for key, value in svin_data.items():
                                line = f"{key}: {value}"
                                file.write(line + "\n")
                            file.write("\n")
            except:
                pass


if __name__ == "__main__":

    base_station = BaseController()
    # base_station.start_survey_in_mode(duration=60,accuracy_=35000)
    # time.sleep(0.2)
    # base_station.svin_message(value=0,layer_=base_station.RAM)
    # time.sleep(0.2)
    # base_station.svin_message(value=0,layer_=base_station.FLASH)
    # time.sleep(0.2)
    #base_station._disable()
    # time.sleep(0.5)
    # base_station.set_fixed_mode(
    #     ecef_x_=-191916128,
    #     ecef_y_=582136888,
    #     ecef_z_=175738897,
    #     accuracy_=120,
    #     layer_=base_station.RAM+base_station.FLASH
    #     )
    # time.sleep(0.5)
    # base_station.enable_RTCM_message(base_station.RAM+base_station.FLASH)
    
