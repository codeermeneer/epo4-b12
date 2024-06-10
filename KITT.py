import serial
import keyboard
import time
import re
import numpy as np
import csv
import pyaudio
from scipy.io import wavfile
import datetime
from threading import Thread

class KITT:
    # class constructor
    # params:
    #   device_index        audio device index
    #   port, baudrate      port and baudrate of the serial connection
    #   carrier_frequency,  OOK beacon parameters
    #   bit_frequency,
    #   repitition_count,
    #   code
    def __init__(
        self, device_index, port, baudrate=115200,
        carrier_frequency=10000,
        bit_frequency=5000,
        repitition_count=2500,
        code=0xDEADBEEF
    ):
        # open an audio stream with the selected device
        self.Fs = 44100
        self.stream = pyaudio_handle.open(input_device_index=device_index,
                                     channels=5,
                                     format=pyaudio.paInt16,
                                     rate=self.Fs,
                                     input=True)

        # open the serial connection to KITT
        self.serial = serial.Serial(port, baudrate, rtscts=True)

        # initialize audio beacon
        self.send_command(f'A0\n')      # start with beacon turned off

        carrier_frequency = carrier_frequency.to_bytes(2, byteorder='big')
        bit_frequency = bit_frequency.to_bytes(2, byteorder='big')
        repitition_count = repitition_count.to_bytes(2, byteorder='big')
        code = code.to_bytes(4, byteorder='big')

        self.serial.write(b'F' + carrier_frequency + b'\n')
        self.serial.write(b'B' + bit_frequency + b'\n')
        self.serial.write(b'R' + repitition_count + b'\n')
        self.serial.write(b'C' + code + b'\n')

        # initialize sensor data array
        self.sensor_data = [['time', 'dist_l', 'dist_r', 'sensor_delay', 'voltage', 'speed', 'angle']]
        self.start_time = time.time()

        # state variables such as speed, angle are defined here
        self.speed = 150
        self.angle = 150

        self.last_dir = "stopped"

        self.logging = True


    # sends the given command via serial
    # command       the command to send
    def send_command(self, command):
        self.serial.write(command.encode())

    # sets the KITT motor to the given speed
    # speed        the speed to give to KITT
    def set_speed(self, speed):
        if speed > 150:
            self.last_dir = "forward"
        elif speed < 150:
            self.last_dir = "backward"

        self.speed = speed

        self.send_command(f'M{speed}\n')

    # sets the KITT wheels to the given angle
    # angle        the angle to give to KITT
    def set_angle(self, angle):
        self.angle = angle
        self.send_command(f'D{angle}\n')

    # stops the motors and straightens the wheels
    def stop(self):
        self.set_speed(150)
        self.set_angle(150)

    # not working yet!
    # emergence brake to quickly stop the vehicle
    def ebrake(self):
        self.set_angle(150)

        #if self.status != "stopped":
        if self.status == "forward":
            print("going back")
            self.set_speed(135)
        elif self.status == "backward":
            print("going forward")
            self.set_speed(165)

        self.set_speed(150)

    # starts the audio beacon
    def start_beacon(self):
        self.send_command(f'A1\n')      # turn on beacon

    # stops the audio beacon
    def stop_beacon(self):
        self.send_command(f'A0\n')      # turn off beacon

    # reads in distance sensor, voltage and delay data
    def read_sensors(self):
        start = time.time()
        t_plus = start - self.start_time

        # read distance sensor
        self.send_command(f'Sd\n')
        status = self.serial.read_until(b'\x04')
        print(status)

        temp = status.decode()
        temp = re.findall(r'\d+', temp)
        res = list(map(int, temp))
        dist_l = res[0]
        dist_r = res[1]

        # read voltage
        self.send_command(f'Sv\n')
        status = self.serial.read_until(b'\x04')
        #print(status)
        temp = status.decode()
        temp = re.findall(r'\d+\.\d+', temp)
        res = list(map(float, temp))
        voltage = res[0]

        # calculate delay time
        end = time.time()
        duration = end - start

        self.sensor_data.append([t_plus, dist_l, dist_r, duration, voltage, self.speed, self.angle])

    def toggle_logs(self):
        self.logging = not self.logging

    # saves the sensor data array to a csv file
    def save_log_data(self):
        # give logs a timestamp so they do not overwrite each other
        timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
        with open("logs/log_%s.csv" % timestamp, "w", newline="") as file:
            mywriter = csv.writer(file, delimiter=",")
            mywriter.writerows(self.sensor_data)

    # clears the sensor data array
    def clear_data(self):
        print("clearing data...")
        self.sensor_data = [['time', 'dist_l', 'dist_r', 'sensor_delay', 'voltage', 'speed', 'angle']]
        self.start_time = time.time()

    # records N samples of audio
    def record(self, N):
        self.start_beacon()
        samples = self.stream.read(N)       # read N samples
        self.stop_beacon()

        # deinterleave channels
        data = np.frombuffer(samples, dtype='int16')
        data = np.reshape(data, (N, 5))
        #data = np.transpose(data)

        # save to file
        wavfile.write("recording.wav", self.Fs, data)

    # deconstructor, stops the car and beacon and then safely closes the serial connection
    def __del__(self):
        self.stop()                     # stop car
        self.send_command(f'A0\n')      # turn off beacon
        self.serial.close()             # close serial connection

        #print(self.sensor_data)         # print final sensor data

# function to control the car using keyboard controls
def wasd(kitt):
    speed = 0
    angle = 0

    while True:
        event = keyboard.read_event()

        if event.event_type == keyboard.KEY_DOWN and event.name == '1':
            if speed > 0:
                speed -= 1
            print("set speed to ", speed)
        if event.event_type == keyboard.KEY_DOWN and event.name == '2':
            if speed < 15:
                speed += 1
            print("set speed to ", speed)
        if event.event_type == keyboard.KEY_DOWN and event.name == '3':
            if angle > 0:
                angle -= 5;
            print("set angle to ", angle)
        if event.event_type == keyboard.KEY_DOWN and event.name == '4':
            if angle < 50:
                angle += 5;
            print("set angle to ", angle)

        if event.event_type == keyboard.KEY_DOWN and event.name == 'w':
            kitt.set_speed(150 + speed)
        if event.event_type == keyboard.KEY_DOWN and event.name == 's':
            kitt.set_speed(150 - speed)
        if event.event_type == keyboard.KEY_DOWN and event.name == 'a':
            kitt.set_angle(150 + angle)
        if event.event_type == keyboard.KEY_DOWN and event.name == 'd':
            kitt.set_angle(150 - angle)

        # stop car or reset wheels when keys are released
        if event.event_type == keyboard.KEY_UP and (event.name == 'w' or event.name == 's'):
            kitt.set_speed(150)
        if event.event_type == keyboard.KEY_UP and (event.name == 'a' or event.name == 'd'):
            kitt.set_angle(150)

        # not working yet
        if event.event_type == keyboard.KEY_DOWN and event.name == 'space':
            print("braking")
            kitt.ebrake()

        if event.event_type == keyboard.KEY_DOWN and event.name == 'e':
            print("starting beacon")
            kitt.start_beacon()
        if event.event_type == keyboard.KEY_DOWN and event.name == 'q':
            print("stopping beacon")
            kitt.stop_beacon()

        # toggle logging
        if event.event_type == keyboard.KEY_DOWN and event.name == 'l':
            kitt.toggle_logs()
            print("Logging:", kitt.logging)
        if event.event_type == keyboard.KEY_DOWN and event.name == 'p':
            print("saving logs..")
            kitt.save_log_data()
        if event.event_type == keyboard.KEY_DOWN and event.name == 'o':
            kitt.clear_data()

        if event.event_type == keyboard.KEY_DOWN and event.name == 'z':
            print("recording...")
            kitt.record(88200)      # record for 2 seconds(2 * Fs samples)

        # exit loop when escape is pressed
        if event.event_type == keyboard.KEY_DOWN and event.name == 'esc':
            print("exiting...")
            kitt.stop()
            break

# predefined route for testing the movement model
def route(kitt):
    input("Press enter to start route")
    start_time = time.time()
    current_time = time.time()
    while current_time - start_time < 5:
        if  current_time - start_time > 2:
            kitt.set_speed(150)
            kitt.set_angle(150)
        elif current_time - start_time > 1:
            kitt.set_speed(165)
            kitt.set_angle(100)
        else:
            kitt.set_speed(165)
            kitt.set_angle(150)
        current_time = time.time()

if __name__ == "__main__":
    comport = "/dev/rfcomm0"

    pyaudio_handle = pyaudio.PyAudio()

    # list audio devices
    for i in range(pyaudio_handle.get_device_count()):
        device_info = pyaudio_handle.get_device_info_by_index(i)
        print(i, device_info['name'])

    device_index = int(input("Please choose an audio device: "))
    device_info = pyaudio_handle.get_device_info_by_index(device_index)
    print(device_info)

    logging_interval = 0.1
    current_time = time.time()
    old_time = 0

    kitt = KITT(device_index, comport)

    wasd_thread = Thread(target=wasd, args=(kitt,))
    wasd_thread.start()
    while wasd_thread.is_alive():
        # read the sensor data each logging interval
        current_time = time.time()
        if kitt.logging and current_time - old_time > logging_interval:
            kitt.read_sensors()
            old_time = current_time

    #route(kitt)
