import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy import integrate
import pandas as pd

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

    # simulate the model for dt seconds
    # phi       steering angle
    # Fa        motor force
    # Fb        breaking force
    # dt        time step
    def sim(self, phi, Fa, Fb, dt):
        Fd = self.b * abs(self.v) + self.c * self.v**2
        Ftot = Fa - (Fd + Fb)
        a = Ftot / self.mass

        self.v += a * dt

        phi = np.radians(phi)
        d = np.array([np.cos(self.alpha),np.sin(self.alpha)])
        d_orth = np.array([-np.sin(self.alpha),np.cos(self.alpha)])

        if phi != 0:  # if the wheels are turned use the turning model
            R = self.length / np.sin(phi)
            circle = self.x + R*d_orth

            omega = (self.v * np.sin(phi))/self.length
            theta = omega * dt
            self.alpha = (self.alpha + theta) % (2*np.pi)

            Rot = np.array([[np.cos(theta), -np.sin(theta)],
                            [np.sin(theta), np.cos(theta)]])

            self.x = circle + np.matmul(Rot, self.x-circle)
        else:       # if the wheels are straight go in a straight line
            self.x = self.x + ((self.v*dt) * d)

        Fd = self.b * abs(self.v) + self.c * self.v**2
        Ftot = Fa - (Fd + Fb)
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
