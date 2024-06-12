import KITTmodel
import KITT
import numpy as np
import matplotlib.pyplot as plt
import math
import serial
import pyaudio
import time

def theta_to_angle(theta):
    max_theta = 30
    slope = -100/(2*max_theta)

    if (theta > max_theta):
        return 100
    elif (theta < -max_theta):
        return 200
    else:
        return slope*theta + 150

m = 5.6
b = 5.25
c = 0.1

L = 0.335
x0 = 0
y0 = 0
alpha0 = 90
v0 = 0

kitt_model = KITTmodel.KITTmodel(m, b, c, L, x0, y0, alpha0, v0)

comport = "/dev/rfcomm0"

pyaudio_handle = pyaudio.PyAudio()

# list audio devices
for i in range(pyaudio_handle.get_device_count()):
    device_info = pyaudio_handle.get_device_info_by_index(i)
    print(i, device_info['name'])

device_index = int(input("Please choose an audio device: "))
device_info = pyaudio_handle.get_device_info_by_index(device_index)
print(device_info)

kitt = KITT.KITT(device_index, comport)

t = 0
dt = 0.01

x_list = []
y_list = []
alpha_list = []
v_list = []
z_list = []
t_list = []

xA = 1.74
yA = 1.62
A = np.array((xA, yA))

finished = False

input("Press enter to start...")

start_time = time.time()
current_time = start_time
while not finished:
    old_time = current_time

    d_car = kitt_model.get_d()
    d_goal = A - kitt_model.get_x()
    distance = np.linalg.norm(d_goal)
    d_goal = d_goal/distance

    if distance < 0.1:
        kitt.ebrake()
        kitt_model.ebrake()
        break
    else:
        speed = 158

    theta = np.arctan(d_car[1]/d_car[0]) - np.arctan(d_goal[1]/d_goal[0])
    print("theta: ", theta)
    if theta > 0:
        angle = 100
    elif theta < 0:
        angle = 200
    else:
        angle = 150
    #angle = theta_to_angle(np.rad2deg(theta))
    #print(angle)

    kitt.set_angle(angle)
    kitt.set_speed(speed)
    kitt_model.set_angle(angle)
    kitt_model.set_speed(speed)

    x_list.append(kitt_model.x[0])
    y_list.append(kitt_model.x[1])
    alpha_list.append(kitt_model.alpha)
    v_list.append(kitt_model.v)
    z_list.append(kitt_model.z)
    t_list.append(current_time)

    current_time = time.time()
    dt = current_time - old_time
    kitt_model.sim(dt)

    if current_time - start_time > 10:
        finished = True

t_list = t_list - np.array(start_time)
fig,a = plt.subplots(2,2, figsize=(10,10))
a[0][0].scatter(x_list, y_list, color='red', s = 1)
a[0][0].scatter(x0, y0, color='blue')
a[0][0].scatter(xA, yA, color='green')
a[0][0].set_xlabel("X position [m]")
a[0][0].set_ylabel("Y Position [m]")
a[0][0].set_title("Position on the field")
a[0][0].set_xlim(0,4.8)
a[0][0].set_ylim(0,4.8)
a[0][0].set_aspect('equal')

a[1][0].plot(t_list, np.degrees(alpha_list))
a[1][0].set_xlabel("Time [s]")
a[1][0].set_ylabel("Orientation [degrees]")
a[1][0].set_title("Orientation of the car")

diffx = x_list - np.array(xA)
diffy = y_list - np.array(yA)
dist = np.sqrt(diffx**2 + diffy**2)

a[0][1].plot(t_list, dist)
a[0][1].set_xlabel("Time [s]")
a[0][1].set_ylabel("Distance [m]")
a[0][1].set_title("Distance to the goal")

a[1][1].plot(t_list, v_list)
a[1][1].set_xlabel("Time [s]")
a[1][1].set_ylabel("Velocity [m/s]")
a[1][1].set_title("Velocity over time")

#plt.savefig("plots/fullmodel.pdf")
plt.show()


