import time
import datetime
import numpy as np
import matplotlib.pyplot as plt
import pyaudio
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

# model input parameters
m = 5.6         # mass of the car
b = 5.25        # drag coefficient
c = 0.1         # air drag coefficient

L = 0.335       # lenght between axles
x0 = 0.2        # initial x position
y0 = 0.25       # initial y position
alpha0 = 90     # initial orientation
v0 = 0          # initial velocity

kitt_model = KITTmodel.KITTmodel(m, b, c, L, x0, y0, alpha0, v0)

COM = "/dev/rfcomm0"

enable_KITT = input("Enter y if you want to enable KITT: ") == 'y'
loc_on = input("Enter y if you want to enable localization: ") == 'y'

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
# use x0,y0 as first localization point
loc_x_list = [x0]
loc_y_list = [y0]

# enter coordinates as a list
goal_list = []
goals = input("Enter your coordinates like this: x,y;x,y;xy;... : ")
goals = goals.split(";")
for goal in goals:
    goal = goal.split(",")
    goal_list.append(np.array((float(goal[0]),float(goal[1]))))

# first goal
goal_index = 0
goal = goal_list[goal_index]
input("Press enter to start...")
# if only one goal is given this will be true and we have Challenge A
last_goal = goal_index == len(goal_list)-1

# timers and timing
loc_interval = 2
logging_interval = 0.1

start_time = time.time()
current_time = start_time
old_time = current_time
last_loc_time = start_time

max_time = 300

finished = False
while not finished:
    # KITT logs
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
        #if dist_to_loc > 0.5:
        if current_time - last_loc_time > loc_interval:
            if enable_KITT:
                kitt.ebrake()
            kitt_model.ebrake()
            old_time = time.time() # update time to prevent large time skips

            print("Localizing...")
            duration = 0.6 # in seconds

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

                # KITTloc returns nan with invalid coordinates
                # this checks for nan values
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
            old_time = time.time() # update time

    # vector from car to goal
    d_goal = goal - kitt_model.get_x()
    #print("d_goal", d_goal)
    distance = np.linalg.norm(d_goal)
    #print("distance", distance)
    d_goal = d_goal/distance        # normalize
    #print("goal", goal)

    if distance < 0.17: # goal is reached
        if enable_KITT:
            kitt.ebrake()
        kitt_model.ebrake()

        if not last_goal:
            print("Waiting 10 seconds...")
            if enable_KITT:
                time.sleep(10)
            old_time = time.time()
            goal_index += 1
            goal = goal_list[goal_index]
            if goal_index == len(goal_list)-1:
                last_goal = True

            d_goal = goal - kitt_model.get_x()
            distance = np.linalg.norm(d_goal)
            d_goal = d_goal/distance

            print("Continuing with challenge B...")
            #input("Press enter to continue")
        else :
            finished = True
            break
    else:   # if goal is not reached continue with driving
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

    # get angle between car dir vector and car to goal vector
    d_car = kitt_model.get_d()
    theta = np.arccos(np.dot(d_car, d_goal))
    d_goal_ccw90 = np.array((-d_goal[1],d_goal[0]))
    if np.dot(d_car, d_goal_ccw90) < 0: # checks if the goal is left or right from car
        theta = -theta  # if product < 0 the goal is to the left and we need a negative angle

    #theta = phi_car - phi_goal
    #print("theta: ", np.rad2deg(theta))
    theta_list.append(np.rad2deg(theta))
    angle = theta_to_angle_1(np.rad2deg(theta)) # convert angles to PWM commands
    #print(angle)

    if enable_KITT:
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
        finished = True

if enable_KITT:
    kitt.save_log_data()



## Plotting
t_list = t_list - np.array(start_time)
fig,a = plt.subplots(2,2, figsize=(10,10))
a[0][0].scatter(x_list, y_list, color='red', s = 1)
a[0][0].scatter(loc_x_list, loc_y_list, color='yellow')
a[0][0].scatter(x0, y0, color='blue')
goal_list = np.transpose(goal_list)
a[0][0].scatter(goal_list[0],goal_list[1], color='green')
a[0][0].set_xlabel("X position [m]")
a[0][0].set_ylabel("Y Position [m]")
a[0][0].set_title("Position on the field")
a[0][0].set_xlim(0,4.6)
a[0][0].set_ylim(0,4.6)
a[0][0].set_aspect('equal')

a[1][0].plot(t_list, theta_list)
#a[1][0].plot(t_list, np.degrees(alpha_list))
a[1][0].set_xlabel("Time [s]")
a[1][0].set_ylabel("Orientation [degrees]")
a[1][0].set_title("Orientation of the car")

a[0][1].plot(t_list, dist_list)
#a[0][1].plot(t_list, theta_list)
#a[0][1].plot(t_list, phi_goal_list)
a[0][1].set_xlabel("Time [s]")
#a[1][0].set_ylabel("Angle [degrees]")
a[0][1].set_ylabel("Distance [m]")
a[0][1].set_title("Distance to the goal")

a[1][1].plot(t_list, v_list)
#a[1][1].plot(t_list, theta_list)
a[1][1].set_xlabel("Time [s]")
a[1][1].set_ylabel("Velocity [m/s]")
a[1][1].set_title("Velocity over time")

timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
plt.savefig("plots/challenge_%s.pdf" % timestamp)
plt.show()
