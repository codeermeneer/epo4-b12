import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy import integrate

class KITTmodel:
    # class constructor
    # m     vehicle mass
    # b     drag coefficient
    # c     air drag coefficient
    # L     distance between the axles of the car
    # x0    initial x position
    # y0    initial y position
    # alpha0    initial orientation of the vehicle
    # v0    initial velocity of the car
    def __init__(self, m, b, c, L, x0, y0, alpha0, v0):
        self.mass = m
        self.b = b
        self.c = c
        self.length = L
        self.x = np.array([x0,y0])
        self.alpha = np.radians(alpha0)
        self.v = v0
        self.z = 0
        self.Fa = 0
        self.Fb = 0
        self.phi = 0

    # sets the KITT motor to the given speed
    # speed        the speed to give to KITT
    def set_speed(self, speed):
        forces = {  150: 0,
                    155: 1.8,
                    156: 2.4,
                    159: 4.8,
                    162: 7.5,
                    165: 8.9  }
        self.Fa = forces[speed]

    # sets the KITT wheels to the given angle
    # angle        the angle to give to KITT
    def set_angle(self, angle):
        angles = {  100: -23.96,
                    115: -17.32,
                    130: -9.89,
                    150: 0,
                    170: 8.86,
                    185: 18.33,
                    200: 26.53  }
        self.phi = angles[angle]

    # simulate the model for dt seconds
    # dt        time step
    def sim(self, dt):
        self.phi = np.radians(self.phi)
        d = np.array([np.cos(self.alpha),np.sin(self.alpha)])
        d_orth = np.array([-np.sin(self.alpha),np.cos(self.alpha)])

        if self.phi != 0:  # if the wheels are turned use the turning model
            R = self.length / np.sin(self.phi)
            circle = self.x + R*d_orth

            omega = (self.v * np.sin(self.phi))/self.length
            theta = omega * dt
            self.alpha = (self.alpha + theta) % (2*np.pi)

            Rot = np.array([[np.cos(theta), -np.sin(theta)],
                            [np.sin(theta), np.cos(theta)]])

            self.x = circle + np.matmul(Rot, self.x-circle)
        else:       # if the wheels are straight go in a straight line
            self.x = self.x + ((self.v*dt) * d)

        Fd = self.b * abs(self.v) + self.c * self.v**2
        Ftot = self.Fa - (Fd + self.Fb)
        a = Ftot / self.mass

        self.v += a * dt

        self.z += abs(self.v * dt)

    def get_x(self):
        return self.x

    def get_alpha(self):
        return self.alpha

    def get_v(self):
        return self.v

    def get_z(self):
        return self.z

    # solved simplified differential equation for v0 = 0
    def vel(self, Fa, Fb, t, v0):
        return (Fa-Fb)/self.b + ((Fb-Fa)/self.b)*np.exp((-self.b*t)/self.mass)
