import serial
import keyboard

class KITT:
    def __init__(self, port, baudrate=115200):
        self.serial = serial.Serial(port, baudrate, rtscts=True)
        # state variables such as speed, angle are defined here

    def send_command(self, command):
        self.serial.write(command.encode())

    def set_speed(self, speed):
        self.send_command(f'M{speed}\n')

    def set_angle(self, angle):
        self.send_command(f'D{angle}\n')

    def stop(self):
        self.set_speed(150)
        self.set_angle(150)

    def __del__(self)
        self.serial.close()

def wasd(kitt):
    # add your code

if __name__ == "__main__":
    # test code follows here
    kitt = KITT("/dev/rfcomm0")
    wasd(kitt)
