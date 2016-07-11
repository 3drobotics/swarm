import subprocess
import time
import os

print "How many copters to simulate: ",
key = raw_input()

cops = int(key)

THREEDR_ROOF_FAR_LEFT = [37.8733607443866,-122.30264715850353]
#THREEDR_ROOF_CENTER = [37.87337688844867,-122.30254221707584]
THREEDR_ROOF_FAR_RIGHT = [37.87342029213903,-122.30243761092424]
THREEDR_ROOF_FAR_RIGHT = THREEDR_ROOF_FAR_LEFT
THREEDR_ROOF_ALT = 4
THREEDR_ROOF_LENGTH_LAT = THREEDR_ROOF_FAR_RIGHT[0] - THREEDR_ROOF_FAR_LEFT[0]
THREEDR_ROOF_LENGTH_LON = THREEDR_ROOF_FAR_RIGHT[1] - THREEDR_ROOF_FAR_LEFT[1]
THREEDR_ROOF_CENTER = [THREEDR_ROOF_FAR_LEFT[0] + (THREEDR_ROOF_LENGTH_LAT)/2, THREEDR_ROOF_FAR_LEFT[1] + (THREEDR_ROOF_LENGTH_LON)/2]
swarm_coords = []
cop_lat, cop_lon = [THREEDR_ROOF_FAR_LEFT[0], THREEDR_ROOF_FAR_LEFT[1]]


for copter in range(cops):
    lat_step = THREEDR_ROOF_LENGTH_LAT/(cops+1)
    lon_step = THREEDR_ROOF_LENGTH_LAT/(cops+1)
    cop_lat = lat_step + cop_lat
    cop_lon = lat_step + cop_lon
    swarm_coords.append(str((cop_lat, cop_lon, THREEDR_ROOF_ALT)))

print "SWARM COORDS: ", swarm_coords



def inplace_change(filename, old_string, new_string):
    s=open(filename).read()
    if old_string in s:
        print 'Changing Simulator Ports from "{old_string}" to "{new_string}"'.format(**locals())
        s=s.replace(old_string, new_string)
        f=open(filename, 'w')
        f.write(s)
        f.flush()
        f.close()
    else:
        print 'No occurances of "{old_string}" found.'.format(**locals())




        
for i in range(14, cops+14):

    filena = "copter"+str(i-13)
    if not os.path.exists((os.path.join(os.path.abspath(os.path.curdir),filena))):
        print "Creating Copter ",i-13        
        subprocess.call(["mkdir",filena])
        
        os.chdir(os.path.join(os.path.abspath(os.path.curdir),filena))
        
        subprocess.call(["git", "clone", "https://github.com/imcnanie/Firmware.git"])
        subprocess.call(["git submodule update --init --recursive"], shell=True)
        #working gazebo commit
	#os.chdir(os.path.join(os.path.abspath(os.path.curdir),"Firmware"))
        #subprocess.call(["git", "reset", "--hard", "8810ee33a4d44fbcc83606c175bff024ce937e68"])
	#os.chdir(os.path.join(os.path.abspath(os.path.curdir),".."))
        time.sleep(1)
        os.chdir(os.path.join(os.path.abspath(os.path.curdir),u'Firmware'))
        if i == 14:
            subprocess.call('cp ../flight_code/ROS/src/burrito/launch/px4_swarm.launch ../flight_code/ROS/src/mavros/mavros/launch/', shell=True)
            subprocess.call('cp ../flight_code/ROS/src/burrito/launch/node_swarm.launch ../flight_code/ROS/src/mavros/mavros/launch/', shell=True)


    else:
        print filena, " exists."
        os.chdir(os.path.join(os.path.abspath(os.path.curdir),filena+'/Firmware'))


    
        

    print "filena"
    old = str(14)
    new = str(i+1)
    path = os.path.abspath(os.path.curdir)
    print "THE PATH: ", path

    try:
        subprocess.call('mv /Tools/jMAVSim/src/me/drton/jmavsim/Simulator.java /Tools/jMAVSim/src/me/drton/jmavsim/Simulator.java.orig', shell=True)
        subprocess.call('cp ../../extras/Simulator.java /Tools/jMAVSim/src/me/drton/jmavsim/Simulator.java', shell=True)
    
        oldsim_str = "public static LatLonAlt DEFAULT_ORIGIN_POS = new LatLonAlt(47.397742, 8.545594, 488);"
        newsim_str = "public static LatLonAlt DEFAULT_ORIGIN_POS = new LatLonAlt"+swarm_coords[i-14]+";"
        print newsim_str
        inplace_change(path+"/Tools/jMAVSim/src/me/drton/jmavsim/Simulator.java", oldsim_str, newsim_str)
    except:
        print "Couldn't fix jMAVsim, please run simulate swarm again when this is finished!"

    inplace_change(path+"/Vagrantfile", old+"556", new+"556")
    inplace_change(path+"/Vagrantfile", old+"560", new+"560")
    inplace_change(path+"/src/modules/mavlink/mavlink_main.cpp", old+"556", new+"556")
    inplace_change(path+"/posix-configs/SITL/init/rcS_gazebo_iris", old+"556", new+"556")
    inplace_change(path+"/posix-configs/SITL/init/rcS_gazebo_iris", old+"557", new+"557")
    inplace_change(path+"/posix-configs/SITL/init/rcS_gazebo_iris", old+"540", new+"540")
    inplace_change(path+"/posix-configs/SITL/init/rcS_jmavsim_iris", old+"556", new+"556")
    inplace_change(path+"/posix-configs/SITL/init/rcS_jmavsim_iris", old+"557", new+"557")
    inplace_change(path+"/posix-configs/SITL/init/rcS_jmavsim_iris", old+"540", new+"540")
    inplace_change(path+"/Tools/CI/MissionCheck.py", old+"540", new+"540")
    inplace_change(path+"/posix-configs/SITL/README.md", old+"550", new+"550")
    inplace_change(path+"/src/modules/mavlink/mavlink_main.cpp", old+"550", new+"550")
    inplace_change(path+"/Tools/sitl_run.sh", old+"560", new+"560")
    inplace_change(path+"/src/modules/simulator/simulator_mavlink.cpp", old+"560", new+"560")
    
   

    
    print 'gnome-terminal '+ '--working-directory='+path+ ' -e \"make posix_sitl_default jmavsim\"'
    subprocess.call('gnome-terminal '+ '--working-directory='+path+ ' -e \"make posix_sitl_default jmavsim"', shell=True)

    os.chdir(os.path.join(os.path.abspath(os.path.curdir),"../.."))
    

