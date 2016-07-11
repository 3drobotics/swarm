#!/usr/bin/env python  
import roslib
import rospy
import tf
import std_msgs
from math import *
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix
import geometry_msgs.msg
import mavros
import mavros_msgs.srv
from mavros import setpoint as SP
from mavros import command
from threading import Thread
from tf.transformations import quaternion_from_euler
from tf.transformations import euler_from_quaternion
import time
import threading
import thread
from random import randint

IS_APM = True
VELOCITY_CAP = 1.0

class posVel:
    def __init__(self, copter_id = "1"):
        self.copter_id = copter_id
        mavros_string = "/copter"+copter_id+"/mavros"
        mavros.set_namespace(mavros_string)  # initialize mavros module with default namespace

        self.mavros_string = mavros_string

        self.final_alt = 0.0
        self.final_pos_x = 0.0
        self.final_pos_y = 0.0        
        self.final_vel = 0.0
        
        self.cur_rad = 0.0
        self.cur_alt = 0.0
        self.cur_pos_x = 0.0
        self.cur_pos_y = 0.0
        self.cur_vel = 0.0

        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0

        self.pose_open = []

        self.alt_control = True
        self.override_nav = False
        self.reached = True
        self.done = False

        self.last_sign_dist = 0.0

        # for local button handling
        self.click = " "
        self.button_sub = rospy.Subscriber("abpause_buttons", std_msgs.msg.String, self.handle_buttons)

        # publisher for mavros/copter*/setpoint_position/local
        self.pub_vel = SP.get_pub_velocity_cmd_vel(queue_size=10)
        # subscriber for mavros/copter*/local_position/local
        self.sub = rospy.Subscriber(mavros.get_topic('local_position', 'local'), SP.PoseStamped, self.temp)

    def handle_buttons(self, msg):
        self.click = str(msg)[6:]

    def temp(self, topic):
        pass

    def start_subs(self):
        pass

    def update(self, com_x, com_y, com_z):
        self.alt_control = True
        self.reached = False
        self.override_nav = False
        self.final_pos_x = com_x
        self.final_pos_y = com_y
        self.final_alt = com_z

        dist = sqrt((self.final_pos_x - self.cur_pos_x)**2 + (self.final_pos_y - self.cur_pos_y)**2)

        return dist

    def set_velocity(self, vel_x, vel_y, vel_z):
        self.override_nav = True
        self.vx = vel_x
        self.vy = vel_y
        self.vz = vel_z

    def subscribe_pose(self):
        rospy.Subscriber(self.mavros_string+'/global_position/local',
                         Odometry,
                         self.handle_pose)
         
        rospy.spin()

    def subscribe_pose_thread(self):
        s = Thread(target=self.subscribe_pose, args=())
        s.daemon = True
        s.start()

    def arm(self):
        arm = rospy.ServiceProxy(self.mavros_string+'/cmd/arming', mavros_msgs.srv.CommandBool)  
        print "Arm: ", arm(True)
        
    def disarm(self):
        arm = rospy.ServiceProxy(self.mavros_string+'/cmd/arming', mavros_msgs.srv.CommandBool)  
        print "Disarm: ", arm(False)

    def setmode(self,base_mode=0,custom_mode="OFFBOARD",delay=0.1):
        set_mode = rospy.ServiceProxy(self.mavros_string+'/set_mode', mavros_msgs.srv.SetMode)  
        if IS_APM:
            if custom_mode == "OFFBOARD":
                custom_mode = "GUIDED"
            if custom_mode == "AUTO.LAND":
                custom_mode = "LAND"
            if custom_mode == "MANUAL":
                custom_mode = "STABILIZE"
            if custom_mode == "POSCTL":
                custom_mode = "LOITER"
        ret = set_mode(base_mode=base_mode, custom_mode=custom_mode)
        print "Changing modes: ", ret
        time.sleep(delay)

    def takeoff_velocity(self, alt=7):
        self.alt_control = False
        if self.cur_alt < alt - 1:
            print "CUR ALT: ", self.cur_alt, "GOAL: ", alt
            #self.set_velocity(0, 0, 1.5)
            self.update(self.cur_pos_x, self.cur_pos_y, alt)
 
        time.sleep(0.1)

        self.final_alt = alt
        
        rospy.loginfo("Reached target Alt!")

    def handle_pose(self, msg):
        pos = msg.pose.pose.position
        qq = msg.pose.pose.orientation

        self.pose_open = qq

        q = (msg.pose.pose.orientation.x,
             msg.pose.pose.orientation.y,
             msg.pose.pose.orientation.z,
             msg.pose.pose.orientation.w)

        euler = euler_from_quaternion(q)

        self.cur_rad = euler[2]

        self.cur_pos_x = pos.x 
        self.cur_pos_y = pos.y
        self.cur_alt = pos.z
        
    def navigate(self):
        rate = rospy.Rate(30)   # 30hz
        magnitude = 0.75  # in meters/sec

        msg = SP.TwistStamped(
            header=SP.Header(
                frame_id="base_footprint",  # doesn't matter
                stamp=rospy.Time.now()),    # stamp should update
        )
        i =0

        self.home_lat = self.cur_pos_x
        self.home_lon = self.cur_pos_y
        self.home_alt = self.cur_alt
        
        while not rospy.is_shutdown():
            if self.click == "ABORT":
                self.disarm()
                break

            if not self.override_nav:  # heavy stuff right about here
                vector_base = self.final_pos_x - self.cur_pos_x
                vector_height = self.final_pos_y - self.cur_pos_y
                try:
                    slope = vector_base/(vector_height+0.000001)
                    p_slope = -vector_height/(vector_base+0.000001)
                except:
                    pass

                copter_rad = self.cur_rad
                vector_rad = atan(slope)
                if self.final_pos_y < self.cur_pos_y:
                    vector_rad = vector_rad - pi

                glob_vx = sin(vector_rad)
                glob_vy = cos(vector_rad)

                beta = ((vector_rad-copter_rad) * (180.0/pi) + 360.0*100.0) % (360.0)
                beta = (beta + 90.0) / (180.0/pi)

                cx = self.cur_pos_x
                cy = self.cur_pos_y
                fx = self.final_pos_x
                fy = self.final_pos_y
                
                b_c = cy - cx * p_slope 
                b_f = fy - fx * p_slope
                sign_dist = b_f - b_c 
                
                if self.last_sign_dist < 0.0 and sign_dist > 0.0:
                    self.reached = True
                if self.last_sign_dist > 0.0 and sign_dist < 0.0:
                    self.reached = True

                self.last_sign_dist = sign_dist 

                if self.reached:
                    self.last_sign_dist = 0.0

                master_scalar = 1.0

                master_hype = sqrt((cx - fx)**2.0 + (cy - fy)**2.0)
                
                if master_hype > 1.0:
                    master_scalar = 1.0
                else:
                    master_scalar = master_hype

                self.vx = sin(beta) * master_scalar
                self.vy = cos(beta) * master_scalar

                        
            if self.alt_control:
                if self.vy > VELOCITY_CAP:
                    self.vy = VELOCITY_CAP
                if self.vy < -VELOCITY_CAP:
                    self.vy = -VELOCITY_CAP
                if self.vx > VELOCITY_CAP:
                    self.vx = VELOCITY_CAP
                if self.vx < -VELOCITY_CAP:
                    self.vx = -VELOCITY_CAP

                if abs(self.final_alt-self.cur_alt) < VELOCITY_CAP:
                    self.vz = (self.final_alt-self.cur_alt)
                else:
                    if self.final_alt > self.cur_alt:
                        self.vz = VELOCITY_CAP
                    if self.final_alt < self.cur_alt:
                        self.vz = -VELOCITY_CAP


                msg.twist.linear = geometry_msgs.msg.Vector3(self.vx*magnitude, self.vy*magnitude, self.vz*magnitude)
            else:
                msg.twist.linear = geometry_msgs.msg.Vector3(self.vx*magnitude, self.vy*magnitude, self.vz*magnitude)


            self.pub_vel.publish(msg)
            
            rate.sleep()
            i += 1

    def land_velocity(self):
        while self.cur_alt > 7.0:
            self.update(self.home_lat, self.home_lon, 7.0)
        self.update(self.home_lat, self.home_lon, 5.0)
        alts = 5.0
        while self.cur_alt < 0.45:
            alts = alts - 0.1
            self.update(self.home_lat, self.home_lon, alts)
            time.sleep(0.5)
        print "Landed, disarming"
        self.update(self.home_lat, self.home_lon, 0)
            
    def get_copter_id(self):
        return self.copter_id
            
    def get_lat_lon_alt(self):
        return (self.cur_pos_x, self.cur_pos_y, self.cur_alt)

    def get_home_lat_lon_alt(self):
        return (self.home_lat, self.home_lon, self.home_alt)

    def start_navigating(self):
        t = Thread(target = self.navigate, args = ())
        t.daemon = True
        t.start()

class SmartRTL:
    def __init__(self, copters):
        self.initial_alt_drop = 5
        self.copters = copters
        self.sorted_copters = []
        copters_by_alt = {}
        for cop in copters:
            copters_by_alt[cop] = cop.get_lat_lon_alt()[-1]

        self.sorted_copters = sorted(copters_by_alt)

        for w in self.sorted_copters[::-1][:-1]:
            self.raise_cops(w)
            
        for x in self.sorted_copters:
            self.land_cop(x)

    def raise_cops(self,cop):
        cur_pos_x, cur_pos_y, cur_alt = cop.get_lat_lon_alt()
        self.raise_height = cur_alt + 5
        cop.update(cur_pos_x, cur_pos_y, self.raise_height)
        while cur_alt < self.raise_height-1:
            cur_pos_x, cur_pos_y, cur_alt = cop.get_lat_lon_alt()
    
    def land_cop(self,cop):
        cur_pos_x, cur_pos_y, cur_alt = cop.get_lat_lon_alt()
        home_lat, home_lon, home_alt = cop.get_home_lat_lon_alt()
        
        print "RTLing Copter", cop.copter_id
        self.drop_height = cur_alt-self.initial_alt_drop
        
        time.sleep(1)
        
        cop.update(cur_pos_x, cur_pos_y, self.drop_height)
        while cur_alt > self.drop_height+2.0:
            cur_pos_x, cur_pos_y, cur_alt = cop.get_lat_lon_alt()
        
        print "Copter", cop.copter_id, "going to home location..."
        time.sleep(1)
        
        cop.update(home_lat, home_lon, self.drop_height)
        while not cop.reached:
            cur_pos_x, cur_pos_y, cur_alt = cop.get_lat_lon_alt()
            time.sleep(0.025)
            
        cop.setmode(custom_mode="AUTO.LAND")

class SafeTakeoff:
    def __init__(self, copters, offsets_x, offsets_y, alt = 20.0, sequential = False):
        self.cops = copters

        self.offs_x = offsets_x
        self.offs_y = offsets_y
        
        self.ids = []
        for i in range(len(self.cops)):
            self.ids.append(i)

        self.alt = alt

        self.sorted_ids = [x for (y,x) in sorted(zip(self.ids, self.ids))]

        self.center_x = self.cops[0].cur_pos_x
        self.center_y = self.cops[0].cur_pos_y

        last = 0

        for i in range(len(self.sorted_ids[::-1])):
            self.cops[i].setmode(custom_mode = "OFFBOARD")

            self.cops[i].arm()

            self.cops[i].takeoff_velocity(alt = alt + i*2.5)

            if sequential:
                while self.cops[i].cur_alt < alt + i*2.5 - 1.0:
                    self.cops[i].update(self.cops[i].cur_pos_x, self.cops[i].cur_pos_y, alt + i*2.5)

            last = i

        while self.cops[last].cur_alt < alt + last*2.5 - 1.0:
            pass
  
        for i in self.sorted_ids[::-1]:
            self.takeoff_cop(i)

        all_reached = 0
        while all_reached < len(self.sorted_ids) - 1:
            all_reached = 0
            for id in self.sorted_ids[::-1]:
                if self.cops[id].reached:
                    all_reached = all_reached + 1

        for i in self.sorted_ids[::-1]:
            self.cops[i].update(self.cops[i].cur_pos_x, self.cops[i].cur_pos_y, alt)

        while abs(self.cops[i].cur_alt - alt) > 1.0:
            pass

    def takeoff_cop(self, id):
        if not self.cops[id].reached:
            self.cops[id].update(self.center_x + self.offs_x[id], self.center_y + self.offs_y[id], self.cops[id].cur_alt)
        
if __name__ == '__main__':
    rospy.init_node("velocity_goto")
    pv = posVel()
    pv.start_subs()
    pv.subscribe_pose_thread()
    time.sleep(0.1)
    pv.start_navigating()
    time.sleep(0.1)
    print "set mode"
    pv.setmode(custom_mode="OFFBOARD")
    pv.arm()
    time.sleep(0.1)
    pv.takeoff_velocity()
    time.sleep(0.1)
    print "out of takeoff"

    # Send copter to current coordinate at 40m
    pv.update(pv.get_lat_lon_alt()[0], pv.get_lat_lon_alt()[1], 40.0)
    
    while not pv.reached:
        time.sleep(0.025)

    print "at gps, waiting"
    time.sleep(2.0)

    print "done"
    
    copters = [pv]
    SmartRTL(copters)

    print "Landed!"

