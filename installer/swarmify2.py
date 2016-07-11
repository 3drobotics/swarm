import urwid
from wifi import Cell, Scheme
import subprocess
import socket
import sys
import paramiko

max_copters = 50

SSID = [x.ssid for x in Cell.all('wlan0') if "SoloLink" in x.ssid ]
SSID_DICT = {}

for x in SSID:
    SSID_DICT[x] = False
    
def menu(title, SSID):
    body = [urwid.Text(title), urwid.Divider()]
    options = []
    for c in SSID:
        button = urwid.Button("[ ] " + c)
        options.append(button)
        #if SSID_DICT[c] == True:
        #    button.set_label(u"DH")
        urwid.connect_signal(button, 'click', item_chosen, c)
        body.append(urwid.AttrMap(button, None, focus_map='reversed'))

    swarmify_button = urwid.Button("Swarmify")
    options.append(swarmify_button)
    urwid.connect_signal(swarmify_button, 'click', swarm_chosen, c)
    body.append(urwid.AttrMap(swarmify_button, None, focus_map='reversed'))
    
    return urwid.ListBox(urwid.SimpleFocusListWalker(body))

def swarm_chosen(button, choice):
    try:
        copters_chosen = [x+ " \n" for x in SSID_DICT.keys() if SSID_DICT[x] == True]
        response = urwid.Text([u'Swarmifying: \n', copters_chosen, u'\n'])
        done = urwid.Button(u'Ok')
        urwid.connect_signal(done, 'click', exit_program)
        main.original_widget = urwid.Filler(urwid.Pile([response,
                                                        urwid.AttrMap(done, None, focus_map='reversed')]))
    except:
        pass


def item_chosen(button, choice):
    if SSID_DICT[choice]:
        button.set_label(u"[ ] " + button.get_label()[4:])
        SSID_DICT[choice] = False
    else:
        button.set_label(u"[*] " + button.get_label()[4:])
        SSID_DICT[choice] = True
        

    
    ##response = urwid.Text([u'You chose ', str(SSID_DICT[choice]), u'\n'])
    ##done = urwid.Button(u'Ok')


    ##urwid.connect_signal(done, 'click', exit_program)
    ##main.original_widget = urwid.Filler(urwid.Pile([response,
    ##urwid.AttrMap(done, None, focus_map='reversed')]))

def exit_program(button):
    raise urwid.ExitMainLoop()

def connect_and_forward(cell_name):
	#This aint working, so just do it manually	
	#cell = Cell.where('wlan0', lambda c: c.ssid == cell_name)[0]
	#scheme = Scheme.for_cell('wlan0', cell_name, cell, passkey="sololink")
	#scheme.activate()
	print "Please connect to the network " + cell_name + " with password sololink"
	print "Follow the instructions on screen"
	subprocess.call("solo wifi --name=BjorkLink --password=bjorklink", shell=True)	

def detect_ports(num_copters):
	for i in range(14,14+max_copters):
  		sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    		port = int(str(i)+str(550))
    		sock.bind(("0.0.0.0", port))
    		sock.settimeout(.1)
    		try:
        		data, addr = sock.recvfrom(1)
        		return str(port)
    		except:
			pass

def forward(artoo, port):
	ssh = paramiko.SSHClient()
	ssh.connect("10.1.1.1", username="root",password="TjSDBkAu")
	ssh.exec_command('iptables -A FORWARD -p udp -d 10.1.1.10 --in-interface wlan0-ap --dport '+port+' -j ACCEPT')
	ssh.exec_command('iptables -A POSTROUTING -t nat --out-interface wlan0 -p udp --dport '+port+' -j MASQUERADE --to ' + port)
	print "Forwarded " +artoo

def change_ports(ip, new_port):
	ssh = paramiko.SSHClient()
	ssh.connect(ip, username="root",password="TjSDBkAu")


main = urwid.Padding(menu(u'Choose Solos to Swarmify', SSID), left=2, right=2)
top = urwid.Overlay(main, urwid.SolidFill(u'\N{MEDIUM SHADE}'),
    align='center', width=('relative', 100),
    valign='middle', height=('relative', 100),
    min_width=20, min_height=9)

urwid.MainLoop(top, palette=[('reversed', 'standout', '')]).run()

active_artoos = [artoo for artoo in SSID_DICT.keys() if SSID_DICT[artoo] == True]
num_copters = len(active_artoos)
ports = []
for network in SSID_DICT.keys():
	if SSID_DICT[network] == True:
		#connect_and_forward(network)
		port = detect_ports(num_copters)
		ports.append(port)
		if port == "14550":
			print artoo + " is still using the default port, so you should probably change it. Terminating."
			sys.exit()
		else:
			forward(network, port)	
			
		
for artoo in active_artoos:
	print network + " on port " + port


	
	
num_copters = len(active_artoos)



