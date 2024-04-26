import serial
import keyboard

class KITT:
    def __init__(
        self, port, baudrate=115200,
        carrier_frequency=10000,
        bit_frequency=5000,
        repitition_count=2500,
        code=0xDEADBEEF
    ):
        self.serial = serial.Serial(port, baudrate, rtscts=True)

        # initialize audio beacon
        self.start_beacon()             # turn on beacon

        self.send_command(f'F{carrier_frequency}\n')
        self.send_command(f'B{bit_frequency}\n')
        self.send_command(f'R{repitition_count}\n')
        self.send_command(f'C{code}\n')

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

    def start_beacon(self):
        self.send_command(f'A1\n')      # turn on beacon

    def stop_beacon(self):
        self.send_command(f'A0\n')      # turn off beacon

    def __del__(self):
        self.stop()                     # stop car
        self.send_command(f'A0\n')      # turn off beacon
        self.serial.close()             # close serial connection

def wasd(kitt):
    while True:
        event = keyboard.read_event()

        if event.event_type == keyboard.KEY_DOWN and event.name == 'w':
            print("going forward")
            kitt.set_speed(165)
        if event.event_type == keyboard.KEY_DOWN and event.name == 's':
            print("going backwards")
            kitt.set_speed(135)
        if event.event_type == keyboard.KEY_DOWN and event.name == 'a':
            print("going left")
            kitt.set_angle(200)
        if event.event_type == keyboard.KEY_DOWN and event.name == 'd':
            print("going right")
            kitt.set_angle(100)

        # stop car or reset wheels when keys are released
        if event.event_type == keyboard.KEY_UP and (event.name == 'w' or event.name == 's'):
            print("stopping motor")
            kitt.set_speed(150)
        if event.event_type == keyboard.KEY_UP and (event.name == 'a' or event.name == 'd'):
            print("resetting wheel angle")
            kitt.set_angle(150)

        if event.event_type == keyboard.KEY_DOWN and event.name == 'e':
            print("starting beacon")
            kitt.start_beacon()
        if event.event_type == keyboard.KEY_DOWN and event.name == 'q':
            print("stopping beacon")
            kitt.stop_beacon()

        # exit loop when escape is pressed
        if event.event_type == keyboard.KEY_DOWN and event.name == 'esc':
            print("exiting...")
            kitt.stop()
            break

if __name__ == "__main__":
    # test code follows here
    comport = input("Please enter your comport: ")
    kitt = KITT(comport)
    wasd(kitt)
