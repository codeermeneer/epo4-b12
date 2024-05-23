import numpy as np
import matplotlib.pyplot as plt

L = 0.335
phi = np.radians(-17.73)
print(phi)

v = 10
alpha = np.radians(0)
x0 = np.array([2.4, 2.3])
d0 = np.array([np.cos(alpha),np.sin(alpha)])
print(d0)

x = x0
d = d0
d_orth = np.array([-np.sin(alpha),np.cos(alpha)])
print(d_orth)

t = 0
dt = 0.01

x_list = []
y_list = []
alpha_list = []
t_list = []

R = L / np.sin(phi)
print("R: ", R)
c = x + R*d_orth
print("c: " , c)
print("shape: ", np.shape(c))

while t<0.5:
    alpha_list.append(alpha)
    t_list.append(t)
    x_list.append(x[0])
    y_list.append(x[1])

    omega = (v * np.sin(phi))/L
    print("omega", omega)
    theta = omega * dt
    print("theta", theta)
    #alpha += theta
    alpha = (alpha + theta) % (2*np.pi)

    Rot = np.array([[np.cos(theta), -np.sin(theta)],
                    [np.sin(theta), np.cos(theta)]])
    print("Rot: ", Rot)

    print("x-c:", x-c)
    tmp = np.matmul(Rot, x-c)
    print("tmp:", tmp)
    x = c + tmp
    print("x:",x)

    d = np.matmul(Rot, d)
    print("d:", d)
    d_orth = np.array([-np.sin(alpha),np.cos(alpha)])
    print("d_orth:", d_orth)

    t += dt

print(x_list)
print(y_list)
#print(alpha_list)

fig,a = plt.subplots(2,2)
a[0][0].scatter(x_list, y_list, color='red')
a[0][0].scatter(x0[0], x0[1], color='blue')
a[0][0].scatter(c[0], c[1], color='black')
a[0][0].set_xlabel("X position [m]")
a[0][0].set_ylabel("Y Position [m]")
#a[0][0].set_title("Distance")
#a[0][0].set_xlim(0,4.8)
#a[0][0].set_ylim(0,2.4)

a[1][0].scatter(t_list, np.degrees(alpha_list))
a[1][0].set_xlabel("Time [s]")
a[1][0].set_ylabel("Orientation [degrees]")

#a[0][0].gca().set_aspect('equal')
plt.show()
