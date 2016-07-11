import socket
import sys
import time
import wifi
import ping
import ssh
import re

ASK_TIME =1
MAX_COPTERS = 100
cont=True
cops = []
ports = {}


def check_yesNo(resp):
	accepted_responses = ["Yes","yes","YES","y","Y"]
	if resp in accepted_responses:
		return True
	else:
		return False
def wait():
	time.sleep(ASK_TIME)

def exit():
	print "Exiting"
	sys.exit()
def wait_for_connected():
	messaged = False
	while True:
		try:
			if(ping.do_one("10.1.1.1",2) != None):
				break
			else:
				if messaged == False:
					print "Are you sure you're connected?"
					messaged = True
				

		except:
			if messaged == False:
				print "Are you sure you're connected?"
				messaged = True
	print "Connected!!"

def detect_ports(silent=False):
	for i in range(14,14+MAX_COPTERS):
  		sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    		port = int(str(i)+str(550))
		print port
    		sock.bind(("0.0.0.0", port))
    		sock.settimeout(.1)
    		try:
        		data, addr = sock.recvfrom(1)
        		return str(port)
    		except:
			pass
		sock.close()
	if silent == False:		
		print "Make sure the solo is connected to the network."
	detect_ports(silent=True)
		

def main():
	"""print "Hello! You've started the swarm install script. This script will guide you through setting up your swarm for flight.\n"
	wait()
	if(check_yesNo(raw_input("Are you ready to start setting up your swarm? (yes/no) ") == False)):
		exit()
	print "\nGreat, let's get started."
	wait()
	print "\nThe first step is to find the copter networks. Please wait while I scan for networks."
	while cont:
		copter_networks = [x.ssid for x in wifi.Cell().all("wlan0") if "SoloLink" in x.ssid]
		if copter_networks == []:
			if(check_yesNo(raw_input("\nNo networks found. Scan again? "))):
				continue
			else:
				exit()
		else:
			break
			
	print "\nI found these networks: "
	print copter_networks
	cops = raw_input("\nPlease enter the copters you would like to swarm in comma seperated form: a,b,c ")
	if(cops == ""):
		exit()
	cops = cops.replace(" ","").split(",")
	"""
	def_ports = []
	for i in range(len(cops)):
		def_ports.append(str(15550+i)
	"""
	print "\nThe next step is to detect which ports the copters are using to send mavlink_data"
	for cop in cops:
		print "\nPlease connect to " + cop +". You have 10 seconds."
		time.sleep(10)
		wait_for_connected()
		ports[cop] = "14550" #detect_ports()
	print "\nThe current port configuration on the copters is: "
	wait()
	for cop in ports.keys():
		print cop + " is on port " + ports[cop]
	wait()
	print "\nI am going to change the configuration to this: "
	wait()
	for cop in cops:
		print "\n" + cop + " will be assigned to port " + def_ports[cops.index(cop)]
 	if(check_yesNo(raw_input("\nContinue? ")) == False):
		exit()
	"""
	ports[0] = "14550"
	for cop in cops:
		if(ports[cop] != def_ports[cops.index(cop)]):
			print "\nPlease connect to " + cop +". You have 10 seconds."
			time.sleep(10)
			wait_for_connected()
			"""client = ssh.ssh_instance()
			client.connect("10.1.1.10")
			soloconf = client.command("cat /etc/sololink.conf")
			new_soloconf = soloconf.replace(re.search("telemDestPort=..550", soloconf).group(0) ,"telemDestPort="+def_ports[cops.index(cop)])
			client.command_blind('echo "' + new_soloconf + '" > /etc/sololink.conf')
			print "echo '" + new_soloconf + "' > /etc/sololink.conf"
			client.command_blind("md5sum /etc/sololink.conf > /etc/sololink.conf.md5")
			client.command_blind("reboot")
			"""
			client = ssh.ssh_instance()
			client.connect("10.1.1.1")
			artooconf = client.command("cat /etc/sololink.conf")
			new_artooconf = artooconf.replace(re.search("telemDestPort=..550", artooconf).group(0),"telemDestPort="+def_ports[cops.index(cop)])
			client.command_blind('echo "' + new_artooconf + '" > /etc/sololink.conf')
			client.command_blind("md5sum /etc/sololink.conf > /etc/sololink.conf.md5")
			client.command_blind("reboot")

		print "\nCopter " + cop + " finished."
	wait()
	f = open("swarm_info",'rw')
	text = ""
	for cop in cops:
		text = text + cop+":"+def_ports[cops.index[cop]]+"\n"
	f.write(text)
	f.close()
	print "\nYour settings have been written to the file swarm_info"
	wait()
	print "\nAll done! Remember to swarm safely."
	
		
		
if __name__=="__main__":
	main()
