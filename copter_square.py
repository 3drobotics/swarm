import time
import rospy
import velocity_goto

print "initializing copters..."

cops = []

for i in range(4):
    cop_num = str(i+1)
    cops.append(velocity_goto.posVel(copter_id = cop_num))

    cops[i].start_subs()
    cops[i].subscribe_pose_thread()

    time.sleep(0.1)

    cops[i].start_navigating()

    time.sleep(0.1)

print "arming copters..."

for c in cops:
    c.setmode(custom_mode = "OFFBOARD")
    c.arm()

    time.sleep(0.1)


