import time
import numpy as np
import matplotlib.pyplot as plt
import pyaudio
import KITTloc
from wavaudioread import wavaudioread
import KITTmodel
import KITT

def theta_to_angle_1(theta_in):
    max_theta = 30
    slope = -100/(2*max_theta)

    if theta_in > max_theta:
        return 100
    if theta_in < -max_theta:
        return 200

    return slope*theta_in + 150

def theta_to_angle_2(theta_in):
    if theta_in > 0:
        return 100
    if theta_in < 0:
        return 200

    return 150

m = 5.6
b = 5.25
c = 0.1

L = 0.335
x0 = 0.2
y0 = 0.25
x0 = 4.6
y0 = 4.6
alpha0 = 90
v0 = 0

kitt_model = KITTmodel.KITTmodel(m, b, c, L, x0, y0, alpha0, v0)

#y_ref = np.array(wavaudioread("ref tests/5000-1000-87.wav", 44100))
#loc = KITTloc.Localization(False, y_ref, 1, 20000)

COM = "/dev/rfcomm0"

enable_KITT = False
if enable_KITT:
# list audio devices
    pyaudio_handle = pyaudio.PyAudio()
    for i in range(pyaudio_handle.get_device_count()):
        device_info = pyaudio_handle.get_device_info_by_index(i)
        print(i, device_info['name'])

    device_index = int(input("Please choose an audio device: "))
    device_info = pyaudio_handle.get_device_info_by_index(device_index)
    print(device_info)

    kitt = KITT.KITT(device_index, COM)
else:
    kitt = None

x_list = []
y_list = []
alpha_list = []
theta_list = []
v_list = []
z_list = []
dist_list = []
phi_goal_list = []
t_list = []
loc_x_list = [x0]
loc_y_list = [y0]


#xA = 4.0
#yA = 2.3
xA = 2.3
yA = 2.3

xB = 2
yB = 4

#x_loc = [0.294, 0.36, 0.371]
#y_loc = [0.486, 0.816, 1.139]
#loc_i = 0

is_chB = True
b_finished = False

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

max_time = 5
if is_chB:
    max_time = 2*max_time + 10

stopped = True
while not finished:
    if enable_KITT:
        if kitt.logging and current_time - old_time > logging_interval:
            kitt.read_sensors()

    old_time = current_time

    if loc_on :
        model_pos = kitt_model.get_x()
        model_x = model_pos[0]
        model_y = model_pos[1]

        new_d = np.array((model_x-loc_x_list[-1],model_y-loc_y_list[-1]))
        dist_to_loc = np.linalg.norm(new_d)
        #print("dt:", current_time-last_loc_time)
        if current_time - last_loc_time > loc_interval:
        #if dist_to_loc > 0.5:
            if enable_KITT:
                kitt.ebrake()
            kitt_model.ebrake()
            stopped = True
            old_time = time.time()
            print("Localizing...")
            duration = 0.6 # in seconds

            #est_x = x_loc[loc_i]
            #est_y = y_loc[loc_i]
            #if (loc_i < 2):
            #    loc_i += 1
            est_x, est_y = float('nan'), float('nan')
            invalid = True
            invalid_count = 0

            while (invalid and invalid_count < 5):
                invalid_count += 1
                if enable_KITT:
                    est_x, est_y = kitt.localize(model_x, model_y, duration)
                else:
                    print("Current model location: ", model_x, ",", model_y)
                    print("KITT disabled please enter localization coordinates:")
                    est_x = float(input("Enter x coordinate: ")) * 100
                    est_y = float(input("Enter y coordinate: ")) * 100

                diffx = est_x/100 - kitt_model.x[0]
                diffy = est_y/100 - kitt_model.x[1]
                dist = np.sqrt(diffx**2 + diffy**2)

                invalid = bool(est_x != est_x or est_y != est_y)

            if invalid_count < 5:
                est_x /= 100
                est_y /= 100

                new_d = np.array((est_x-loc_x_list[-1],est_y-loc_y_list[-1]))
                new_d = new_d/np.linalg.norm(new_d)
                kitt_model.set_x(est_x, est_y)
                kitt_model.set_d(new_d[0], new_d[1])
                loc_x_list.append(est_x)
                loc_y_list.append(est_y)
                print("Position: (", est_x, ", ", est_y, ")")
                last_loc_time = time.time()
            else :
                print("No valid location found, continuing with model...")
            #input("Localizing done, press enter to continue...")
            old_time = time.time()

    d_goal = goal - kitt_model.get_x()
    #print("d_goal", d_goal)
    distance = np.linalg.norm(d_goal)
    #print("distance", distance)
    d_goal = d_goal/distance
    #print("goal", goal)

    if distance < 0.17:
        if enable_KITT:
            kitt.ebrake()
        kitt_model.ebrake()
        stopped = True
        if (is_chB and (not b_finished)):
            b_finished = True
            print("Waiting 10 seconds...")
            if enable_KITT:
                time.sleep(10)
            old_time = time.time()
            x_goal = xB
            y_goal = yB
            goal = np.array((x_goal, y_goal))

            d_goal = goal - kitt_model.get_x()
            distance = np.linalg.norm(d_goal)
            d_goal = d_goal/distance

            print("Continuing with challenge B...")
            #input("Press enter to continue")
        else :
            finished = True
            break
    else:
        speed = 158


#    phi_car = kitt_model.get_alpha()
#
#    phi_goal = np.arctan(d_goal[1]/d_goal[0])
#    if (d_goal[0] < 0 and d_goal[1] < 0):
#        phi_goal -= np.pi
#    elif d_goal[0] < 0:
#        phi_goal += np.pi

    #if phi_goal < 0:
    #    phi_goal = 360 - phi_goal

    d_car = kitt_model.get_d()
    theta = np.arccos(np.dot(d_car, d_goal))
    d_goal_ccw90 = np.array((-d_goal[1],d_goal[0]))
    if np.dot(d_car, d_goal_ccw90) < 0:
        theta = -theta

    #theta = phi_car - phi_goal
    #print("theta: ", np.rad2deg(theta))
    theta_list.append(np.rad2deg(theta))
    angle = theta_to_angle_1(np.rad2deg(theta))
    #print(angle)

    if enable_KITT:
        kitt.set_angle(int(angle))
        kitt.set_speed(speed)
    kitt_model.set_angle(angle)
    kitt_model.set_speed(speed)

    #if (stopped) :
    #    time.sleep(0.5)
    #    stopped = False

    x_list.append(kitt_model.x[0])
    y_list.append(kitt_model.x[1])
    alpha_list.append(kitt_model.alpha)
    v_list.append(kitt_model.v)
    z_list.append(kitt_model.z)
    t_list.append(current_time)
    dist_list.append(distance)
    #phi_goal_list.append(np.rad2deg(phi_goal))

    current_time = time.time()
    #print("t: ", current_time - start_time)
    dt = current_time - old_time
    kitt_model.sim(dt)

    if current_time - start_time > max_time:
        if enable_KITT:
            kitt.ebrake()
        kitt_model.ebrake()
        stopped = True
        finished = True

if enable_KITT:
    kitt.save_log_data()



## Plotting
t_list = t_list - np.array(start_time)
fig,a = plt.subplots(2,2, figsize=(10,10))
a[0][0].scatter(x_list, y_list, color='red', s = 1)
a[0][0].scatter(loc_x_list, loc_y_list, color='yellow')
a[0][0].scatter(x0, y0, color='blue')
a[0][0].scatter(xA, yA, color='green')
if is_chB:
    a[0][0].scatter(xB, yB, color='pink')
a[0][0].set_xlabel("X position [m]")
a[0][0].set_ylabel("Y Position [m]")
a[0][0].set_title("Position on the field")
a[0][0].set_xlim(0,4.8)
a[0][0].set_ylim(0,4.8)
#a[0][0].set_aspect('equal')

a[1][0].scatter(t_list, np.degrees(alpha_list), s=1)
a[1][0].set_xlabel("Time [s]")
a[1][0].set_ylabel("Orientation [degrees]")
a[1][0].set_title("Orientation of the car")

#a[0][1].plot(t_list, dist_list)
#a[0][1].plot(t_list, theta_list)
#a[0][1].plot(t_list, phi_goal_list)
a[0][1].set_xlabel("Time [s]")
#a[1][0].set_ylabel("Angle [degrees]")
a[0][1].set_ylabel("Distance [m]")
a[0][1].set_title("Distance to the goal")

#a[1][1].plot(t_list, v_list)
a[1][1].plot(t_list, theta_list)
a[1][1].set_xlabel("Time [s]")
a[1][1].set_ylabel("Velocity [m/s]")
a[1][1].set_title("Velocity over time")

#plt.savefig("plots/fullmodel.pdf")
plt.show()
