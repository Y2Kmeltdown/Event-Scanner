import serial
import time

class Actuator:
    def __init__(self, port: str) -> None:
        self.serial = serial.Serial(port, baudrate=115200, timeout=1.0)
        time.sleep(3.0)

    def reset(self):
        self.serial.write(bytes([0xFF, 0xFF]))

    def move(self, position: int):
        assert position >= -1000 and position <= 1000
        position += 1500
        self.serial.write(bytes([position & 0xFF, (position >> 8) & 0xFF]))
