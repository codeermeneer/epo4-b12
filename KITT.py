import serial
import keyboard
import time
import re
import numpy as np
import csv
import pyaudio
from scipy.io import wavfile
import datetime

class KITT:
    def __init__(
        self, device_index, port, baudrate=115200,
        carrier_frequency=10000,
        bit_frequency=5000,
        repitition_count=2500,
        code=0xDEADBEEF
    ):
        self.Fs = 44100
        self.stream = pyaudio_handle.open(input_device_index=device_index,
                                     channels=5,
                                     format=pyaudio.paInt16,
                                     rate=self.Fs,
                                     input=True)

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
        self.sensor_data = [['time', 'dist_l', 'dist_r', 'sensor_delay', 'voltage']]
        self.start_time = time.time()


        # state variables such as speed, angle are defined here
        self.last_dir = "stopped"


    def send_command(self, command):
        self.serial.write(command.encode())

    def set_speed(self, speed):
        if speed > 150:
            self.last_dir = "forward"
        elif speed < 150:
            self.last_dir = "backward"

        self.send_command(f'M{speed}\n')

    def set_angle(self, angle):
        self.send_command(f'D{angle}\n')

    def stop(self):
        self.set_speed(150)
        self.set_angle(150)

    def ebrake(self):
        #if self.status != "stopped":
        if self.status == "forward":
            print("going back")
            self.set_speed(135)
        elif self.status == "backward":
            print("going forward")
            self.set_speed(165)

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
        #print(dist_l)
        #print(dist_r)

        self.send_command(f'Sv\n')
        status = self.serial.read_until(b'\x04')
        print(status)
        temp = status.decode()
        temp = re.findall(r'\d+\.\d+', temp)
        res = list(map(float, temp))
        voltage = res[0]

        end = time.time()
        duration = end - start
        print(f"{duration} seconds")

        self.sensor_data.append([t_plus, dist_l, dist_r, duration, voltage])

    def save_log_data(self):
        timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
        with open("logs/log_%s.csv" % timestamp, "w", newline="") as file:
            mywriter = csv.writer(file, delimiter=",")
            mywriter.writerows(self.sensor_data)

    def clear_data(self):
        print("clearing data...")
        self.sensor_data = [['time', 'dist_l', 'dist_r', 'sensor_delay', 'voltage']]
        self.start_time = time.time()

    def record(self, N):
        self.start_beacon()
        samples = self.stream.read(N)
        self.stop_beacon()
        data = np.frombuffer(samples, dtype='int16')
        data = np.reshape(data, (N, 5))
        data = np.transpose(data)
        wavfile.write("ch1.wav", self.Fs, data[0])
        wavfile.write("ch2.wav", self.Fs, data[1])
        wavfile.write("ch3.wav", self.Fs, data[2])
        wavfile.write("ch4.wav", self.Fs, data[3])
        wavfile.write("ch5.wav", self.Fs, data[4])

    def __del__(self):
        self.stop()                     # stop car
        self.send_command(f'A0\n')      # turn off beacon
        self.serial.close()             # close serial connection

        print(self.sensor_data)
        #print(delays)

def wasd(kitt):
    logging = True
    logging_interval = 0.5
    current_time = time.time()
    old_time = 0
    speed = 0

    while True:
        event = keyboard.read_event()

        current_time = time.time()
        if logging and current_time - old_time > logging_interval:
            kitt.read_sensors()
            old_time = current_time

        if event.event_type == keyboard.KEY_DOWN and event.name == '1':
            #speed = 4
            if speed > 0:
                speed -= 1
            print("set speed to ", speed)
        if event.event_type == keyboard.KEY_DOWN and event.name == '2':
            #speed = 6
            if speed < 15:
                speed += 1
            print("set speed to ", speed)
        if event.event_type == keyboard.KEY_DOWN and event.name == '3':
            speed = 9
            print("set speed to ", speed)
        if event.event_type == keyboard.KEY_DOWN and event.name == '4':
            speed = 12
            print("set speed to ", speed)
        if event.event_type == keyboard.KEY_DOWN and event.name == '5':
            speed = 15
            print("set speed to ", speed)

#        if event.event_type == keyboard.KEY_DOWN and event.name == 'minus':
#            if speed > 0:
#                speed -= 1
#            print("set speed to ", speed)
#        if event.event_type == keyboard.KEY_DOWN and event.name == '=':
#            if speed < 15:
#                speed += 1
#            print("set speed to ", speed)

        if event.event_type == keyboard.KEY_DOWN and event.name == 'w':
            #print("going forward")
            kitt.set_speed(150 + speed)
        if event.event_type == keyboard.KEY_DOWN and event.name == 's':
            #print("going backwards")
            kitt.set_speed(150 - speed)
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

        if event.event_type == keyboard.KEY_DOWN and event.name == 'space':
            print("braking")
            kitt.ebrake()

        if event.event_type == keyboard.KEY_DOWN and event.name == 'e':
            print("starting beacon")
            kitt.start_beacon()
        if event.event_type == keyboard.KEY_DOWN and event.name == 'q':
            print("stopping beacon")
            kitt.stop_beacon()

        if event.event_type == keyboard.KEY_DOWN and event.name == 'l':
            #kitt.read_sensors()
            logging != logging
        if event.event_type == keyboard.KEY_DOWN and event.name == 'p':
            print("saving logs..")
            kitt.save_log_data()
        if event.event_type == keyboard.KEY_DOWN and event.name == 'o':
            kitt.clear_data()

        if event.event_type == keyboard.KEY_DOWN and event.name == 'z':
            print("recording...")
            kitt.record(88200)

        # exit loop when escape is pressed
        if event.event_type == keyboard.KEY_DOWN and event.name == 'esc':
            print("exiting...")
            kitt.stop()
            break

if __name__ == "__main__":
    # test code follows here
    #comport = input("Please enter your comport: ")
    comport = "/dev/rfcomm0"

    pyaudio_handle = pyaudio.PyAudio()

    for i in range(pyaudio_handle.get_device_count()):
        device_info = pyaudio_handle.get_device_info_by_index(i)
        print(i, device_info['name'])

    device_index = int(input("Please choose an audio device: "))
    device_info = pyaudio_handle.get_device_info_by_index(device_index)
    print(device_info)
    kitt = KITT(device_index, comport)
    wasd(kitt)
