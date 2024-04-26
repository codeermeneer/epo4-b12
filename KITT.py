import serial
import keyboard
import time
import re
import numpy as np
import csv

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
        #self.start_beacon()             # turn on beacon
        self.send_command(f'A0\n')      # turn off beacon

        carrier_frequency = carrier_frequency.to_bytes(2, byteorder='big')
        bit_frequency = bit_frequency.to_bytes(2, byteorder='big')
        repitition_count = repitition_count.to_bytes(2, byteorder='big')
        code = code.to_bytes(4, byteorder='big')

        self.serial.write(b'F' + carrier_frequency + b'\n')
        self.serial.write(b'B' + bit_frequency + b'\n')
        self.serial.write(b'R' + repitition_count + b'\n')
        self.serial.write(b'C' + code + b'\n')

        #self.delays = []
        self.sensor_data = [['time', 'dist_l', 'dist_r']]
        self.start_time = time.time()


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

    def read_sensors(self):
        start = time.time()
        t_plus = start - self.start_time

        self.send_command(f'Sd\n')
        status = self.serial.read_until(b'\x04')
        print(status)

        temp = status.decode()
        temp = re.findall(r'\d+', temp)
        res = list(map(int, temp))
        dist_l = res[0]
        dist_r = res[1]
        print(dist_l)
        print(dist_r)

        end = time.time()
        duration = end - start
        print(f"{duration} seconds")
        #self.delays.append(duration)

        self.sensor_data.append([t_plus, dist_l, dist_r])

    def save_sensor_data(self):
        with open("sensors.csv", "w", newline="") as file:
            mywriter = csv.writer(file, delimiter=",")
            mywriter.writerows(self.sensor_data)

    def __del__(self):
        self.stop()                     # stop car
        self.send_command(f'A0\n')      # turn off beacon
        self.serial.close()             # close serial connection

        print(self.sensor_data)
        #print(delays)

def wasd(kitt):
    while True:
        event = keyboard.read_event()

        if event.event_type == keyboard.KEY_DOWN and event.name == 'w':
            #print("going forward")
            kitt.set_speed(165)
        if event.event_type == keyboard.KEY_DOWN and event.name == 's':
            #print("going backwards")
            kitt.set_speed(135)
        if event.event_type == keyboard.KEY_DOWN and event.name == 'a':
            #print("going left")
            kitt.set_angle(200)
        if event.event_type == keyboard.KEY_DOWN and event.name == 'd':
            #print("going right")
            kitt.set_angle(100)

        # stop car or reset wheels when keys are released
        if event.event_type == keyboard.KEY_UP and (event.name == 'w' or event.name == 's'):
            #print("stopping motor")
            kitt.set_speed(150)
        if event.event_type == keyboard.KEY_UP and (event.name == 'a' or event.name == 'd'):
            #print("resetting wheel angle")
            kitt.set_angle(150)

        if event.event_type == keyboard.KEY_DOWN and event.name == 'e':
            print("starting beacon")
            kitt.start_beacon()
        if event.event_type == keyboard.KEY_DOWN and event.name == 'q':
            print("stopping beacon")
            kitt.stop_beacon()

        if event.event_type == keyboard.KEY_DOWN and event.name == 'r':
            kitt.read_sensors()
        if event.event_type == keyboard.KEY_DOWN and event.name == 't':
            print("saving sensor data..")
            kitt.save_sensor_data()

        # exit loop when escape is pressed
        if event.event_type == keyboard.KEY_DOWN and event.name == 'esc':
            print("exiting...")
            kitt.stop()
            break

if __name__ == "__main__":
    # test code follows here
    #comport = input("Please enter your comport: ")
    comport = "/dev/rfcomm0"
    kitt = KITT(comport)
    wasd(kitt)
