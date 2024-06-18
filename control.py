import KITTmodel
import KITT
import numpy as np
import matplotlib.pyplot as plt
import math
import serial
import pyaudio
import time
import KITTloc
from wavaudioread import wavaudioread

def theta_to_angle_1(theta):
    max_theta = 30
    slope = -100/(2*max_theta)

    if (theta > max_theta):
        return 100
    elif (theta < -max_theta):
        return 200
    else:
        return slope*theta + 150

def theta_to_angle_2(theta):
    if (theta > 0):
        return 100
    elif (theta < 0):
        return 200
    else:
        return 150

m = 5.6
b = 5.25
c = 0.1

L = 0.335
x0 = 0.2
y0 = 0.25
alpha0 = 90
v0 = 0

kitt_model = KITTmodel.KITTmodel(m, b, c, L, x0, y0, alpha0, v0)

y_ref = np.array(wavaudioread("ref tests/5000-1000-87.wav", 44100))
loc = KITTloc.Localization(False, y_ref, 1, 20000)

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
theta_list = []
v_list = []
z_list = []
t_list = []
loc_x_list = []
loc_y_list = []


xA = 3.10
yA = 2.49
#xA = 2.30
#yA = 2.30

x_loc = [0.294, 0.36, 0.371]
y_loc = [0.486, 0.816, 1.139]
loc_i = 0

is_chB = False
b_finished = False

xB = 1
yB = 4

x_goal = xA
y_goal = yA
goal = np.array((x_goal, y_goal))
input("Press enter to start...")

loc_interval = 2
logging_interval = 0.1
loc_on = False

start_time = time.time()
current_time = start_time
old_time = current_time
last_loc_time = start_time
finished = False
while not finished:
    if kitt.logging and current_time - old_time > logging_interval:
        kitt.read_sensors()

    old_time = current_time

    if (loc_on) :
        #print("dt:", current_time-last_loc_time)
        if (current_time - last_loc_time > loc_interval):
            kitt.ebrake()
            kitt_model.ebrake()
            old_time = time.time()
            print("Localizing...")
            duration = 1 # in seconds
            model_pos = kitt_model.get_x()
            model_x = model_pos[0]
            model_y = model_pos[1]

            #est_x = x_loc[loc_i]
            #est_y = y_loc[loc_i]
            #if (loc_i < 2):
            #    loc_i += 1
            est_x, est_y = float('nan'), float('nan')
            invalid = True
            invalid_count = 0

            while (invalid and invalid_count < 5):
                invalid_count += 1
                est_x, est_y = kitt.localize(model_x, model_y, duration)

                diffx = est_x/100 - kitt_model.x[0]
                diffy = est_y/100 - kitt_model.x[1]
                dist = np.sqrt(diffx**2 + diffy**2)

                if (est_x != est_x or est_y != est_y):
                    invalid = True
                else :
                    invalid = False

            if invalid_count < 5:
                est_x /= 100
                est_y /= 100
                kitt_model.set_x(est_x, est_y)
                loc_x_list.append(est_x)
                loc_y_list.append(est_y)
                print("Position: (", est_x, ", ", est_y, ")")
                last_loc_time = time.time()
            else :
                print("No valid location found, continuing with model...")
            #input("Localizing done, press enter to continue...")

    d_car = kitt_model.get_d()
    d_goal = goal - kitt_model.get_x()
    distance = np.linalg.norm(d_goal)
    d_goal = d_goal/distance

    if distance < 0.1:
        kitt.ebrake()
        kitt_model.ebrake()
        if (is_chB and (not b_finished)):
            b_finished = True
            print("Waiting 10 seconds...")
            time.sleep(10)
            old_time = time.time()
            x_goal = xB
            y_goal = yB
            goal = np.array((x_goal, y_goal))
            print("Continuing with challenge B...")
            #input("Press enter to continue")
        else :
            finished = True
            break
    else:
        speed = 158

#    phi_car = np.arctan(d_car[1]/d_car[0])
#    if (d_car[0] < 0 and d_car[1] < 0):
#        phi_car -= np.pi
#    elif (d_car[0] < 0):
#        phi_car += np.pi

    phi_goal = np.arctan(d_goal[1]/d_goal[0])
    if (d_goal[0] < 0 and d_goal[1] < 0):
        phi_goal -= np.pi
    elif (d_goal[0] < 0):
        phi_goal += np.pi


    theta = kitt_model.get_alpha() - phi_goal
    #theta = phi_car - phi_goal
    #print("theta: ", np.rad2deg(theta))
    theta_list.append(np.rad2deg(theta))
    angle = theta_to_angle_1(np.rad2deg(theta))
    #print(angle)

    kitt.set_angle(int(angle))
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
        kitt.ebrake()
        kitt_model.ebrake()
        finished = True

kitt.save_log_data

t_list = t_list - np.array(start_time)
fig,a = plt.subplots(2,2, figsize=(10,10))
a[0][0].scatter(x_list, y_list, color='red', s = 1)
a[0][0].scatter(loc_x_list, loc_y_list, color='yellow')
a[0][0].scatter(x0, y0, color='blue')
a[0][0].scatter(xA, yA, color='green')
if (is_chB):
    a[0][0].scatter(xB, yB, color='pink')
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
#a[0][1].plot(t_list, theta_list)
a[0][1].set_xlabel("Time [s]")
a[1][0].set_ylabel("Angle [degrees]")
a[0][1].set_ylabel("Distance [m]")
a[0][1].set_title("Distance to the goal")

a[1][1].plot(t_list, v_list)
a[1][1].set_xlabel("Time [s]")
a[1][1].set_ylabel("Velocity [m/s]")
a[1][1].set_title("Velocity over time")

#plt.savefig("plots/fullmodel.pdf")
plt.show()
