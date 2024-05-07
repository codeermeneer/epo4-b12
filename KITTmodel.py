import numpy as np
import matplotlib.pyplot as plt
from scipy import integrate

m = 5.6
b = 5
c = 0.1
Fa = 10
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
plt.show()
