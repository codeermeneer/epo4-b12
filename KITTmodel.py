import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy import integrate
import pandas as pd

m = 5.6
b = 5
c = 0.1
Fa = 9.2
Fb = 0
Fd = 0

a = 0
v = 0
z = 0
t = 0
dt = 0.01

v_list = []
z_list = []
t_list = []

def vel(t, v0):
    return (Fa-Fb)/b + ((Fb-Fa)/b)*np.exp((-b*t)/m)

while t < 8:
    Fd = b * abs(v) + c * v**2
    Ftot = Fa - (Fd + Fb)
    a = Ftot / m
    v += a * dt
    z += v * dt
    v_list.append(v)
    z_list.append(z)
    t_list.append(t)
    t += dt

t = np.linspace(0, 8, 1000)
v = vel(t,0)
z = integrate.cumtrapz(v,t, initial=0)

fig,a = plt.subplots(2,2)

a[0][0].plot(t_list, z_list, color='red')
a[0][0].plot(t, z, color='blue')
a[0][0].set_xlabel("Time [s]")
a[0][0].set_ylabel("Z Position [m]")
a[0][0].set_title("Distance")

a[1][0].plot(t_list, v_list, color='red')
a[1][0].plot(t, v, color='blue')
a[1][0].set_xlabel("Time [s]")
a[1][0].set_ylabel("Velocity [m/s]")
a[1][0].set_title("Velocity")

a[0][1].plot(t_list, z_list, color='red')
a[0][1].plot(t, z, color='blue')
a[0][1].set_xlabel("Time [s]")
a[0][1].set_ylabel("Z Position [m]")
a[0][1].set_title("Distance")

a[1][1].plot(t_list, v_list, color='red')
a[1][1].plot(t, v, color='blue')
a[1][1].set_xlabel("Time [s]")
a[1][1].set_ylabel("Velocity [m/s]")
a[1][1].set_title("Velocity")

data = pd.read_csv("logs/motor/165.csv")
distances = ((data['dist_r'].values + data['dist_l']) / 2)/100
distances = distances[0] - distances
time = data['time'].values
time = time - time[0]

a[0][0].scatter(time, distances, color='green')

velocity = []
for i in range(1,len(distances)):
    velocity.append((distances[i]-distances[i-1])/(time[i]-time[i-1]))
vel_time = []
for i in range(1,len(time)):
    vel_time.append(time[i-1]+((time[i] - time[i-1])/2))

print(time)
print(vel_time)

a[1][0].scatter(vel_time, velocity, color='green')
a[0][0].set_xlim(0, 8)
a[1][0].set_xlim(0, 8)

print(data)
data = pd.read_csv("logs/motor/165.csv")
distances = ((data['dist_r'].values + data['dist_l']) / 2)/100
distances = distances[0] - distances
time = data['time'].values
time = time - time[0]
velocity = [0]
for i in range(1,len(distances)):
    velocity.append((distances[i]-distances[i-1])/(time[i]-time[i-1]))


a[0][1].scatter(time, distances, color='green')
a[1][1].scatter(time, velocity, color='green')

plt.show()
