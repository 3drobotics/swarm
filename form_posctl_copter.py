from nav_msgs.msg import Odometry
import std_msgs
import rosnode
import roslib
import rospy
import tf

from threading import Thread
from math import *
import time
import ast
import os

import velocity_goto

class artoo:
    def __init__(self):
        self.stick_map = []

        self.mod_scalar = 1.0

        self.x_offset = 0.0
        self.y_offset = 0.0
        self.z_offset = 0.0

        self.fin_x = 0.0
        self.fin_y = 0.0
        self.fin_z = 0.0

        for i in range(8):
            self.stick_map.append(0.0)

    def handle_sticks(self, msg):
        unpack = ast.literal_eval(str(msg)[6:])

        raw_stick = []

        for i in unpack:
            raw_stick.append(float(int(i)-1500)/500)

        try:
            for r in range(8):
                self.stick_map[r] = raw_stick[r]
        except:
            pass

        self.x_offset = self.stick_map[1] * self.mod_scalar
        self.y_offset = -self.stick_map[2] * self.mod_scalar
        self.z_offset = self.stick_map[0]

    def start_subbing(self):
        stick_sub = rospy.Subscriber("sticks", std_msgs.msg.String, self.handle_sticks)

rospy.init_node("copter_broadcast_frames")

print "initializing copter..."

cops = []

for i in range(2):
    print str(i+1)
    cops.append(velocity_goto.posVel(copter_id = str(i+1)))

for cop in cops:
    cop.start_subs()
    time.sleep(1.0)

    cop.subscribe_pose_thread()
    time.sleep(0.1)

    cop.start_navigating()
    time.sleep(0.1)

print "taking off"

i = 1

for cop in cops:
    print i
    cop.setmode(custom_mode = "OFFBOARD")
    cop.arm()
    time.sleep(0.1)

    cop.takeoff_velocity()

    i = i +1

print "ready"

a = artoo()
a.start_subbing()

a.fin_x = cops[0].cur_pos_x
a.fin_y = cops[0].cur_pos_y
a.fin_z = cops[0].cur_alt

offs_x = [0.0, 2.0, 0.0, 2.0]
offs_y = [0.0, 0.0, 2.0, 2.0]

while True:
    io = 0

    for cop in cops:
        if abs(a.stick_map[0]) < 0.01 and abs(a.stick_map[1]) < 0.01 and abs(a.stick_map[2]) < 0.01:
            a.fin_x = cops[0].cur_pos_x + offs_x[io]
            a.fin_y = cops[0].cur_pos_y + offs_y[io]
            a.fin_z = cops[0].cur_alt
        else:
            a.fin_x = cops[0].cur_pos_x + a.x_offset + offs_x[io]
            a.fin_y = cops[0].cur_pos_y + a.y_offset + offs_y[io]
            a.fin_z = cops[0].cur_alt + a.z_offset

        cop.update(a.fin_x, a.fin_y, a.fin_z)

        time.sleep(0.1)

        io = io + 1 


