import ssh

timeout = """
if [ "$#" -lt "2" ]; then
    echo "Usage:   `basename $0` timeout_in_seconds command" >&2
    echo "Example: `basename $0` 2 sleep 3 || echo timeout" >&2
    exit 1
fi

cleanup()
{
    trap - ALRM               #reset handler to default
    kill -ALRM $a 2>/dev/null #stop timer subshell if running
    kill $! 2>/dev/null &&    #kill last job
      exit 124                #exit with 124 if it was running
}

watchit()
{
    trap "cleanup" ALRM
    sleep $1& wait
    kill -ALRM $$
}

watchit $1& a=$!         #start the timeout
shift                    #first param was timeout for sleep
trap "cleanup" ALRM INT  #cleanup after timeout
"$@"& wait $!; RET=$?    #start the job wait for it and save its return 
value
kill -ALRM $a            #send ALRM signal to watchit
wait $a                  #wait for watchit to finish cleanup
exit $RET                #return the value
"""

setupwifi = """
# Delete old files
rm /mnt/rootfs.rw/lib/modules/3.10.17-rt12-*/kernel/net/ipv4/netfilter/iptable_filter.ko || true

/etc/init.d/hostapd stop
killall wpa_supplicant || true
killall udhcpc || true

cat <<EOF > /etc/wpa_client.conf
network={
%s
}
EOF

echo 1 > /proc/sys/net/ipv4/ip_forward

sed -i.bak 's/dhcp-option=3.*/dhcp-option=3,10.1.1.1/g' 
/etc/dnsmasq.conf
sed -i.bak 's/dhcp-option=6.*/dhcp-option=6,8.8.8.8/g' /etc/dnsmasq.conf

/etc/init.d/dnsmasq restart
sleep 2

echo 'connecting to the internet...'
wpa_supplicant -i wlan0 -c /etc/wpa_client.conf -B

/etc/timeout.sh 15 udhcpc -i wlan0 || {
    ifconfig wlan0 down
}

/etc/init.d/hostapd start

sleep 3
wget -O- http://example.com/ --timeout=5 >/dev/null 2>&1
if [[ $? -ne '0' ]]; then
    echo ''
    echo 'error: could not connect to the Internet!'
    echo 'please check your wifi credentials and try again.'
else
    echo 'setting up IP forwarding...'
    insmod /lib/modules/3.10.17-rt12-*/kernel/net/ipv4/netfilter/iptable_filter.ko 2>/dev/null
    iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
    iptables -A FORWARD -i wlan0 -o wlan0-ap -j ACCEPT
    iptables -A FORWARD -i wlan0-ap -o wlan0 -j ACCEPT
    echo ''
    echo 'success: Solo is now connected to the Internet.'
    echo 'if your computer does not yet have Internet access, try'
    echo 'disconnecting and reconnecting to Solo wifi network.'
fi
"""

rclocal = """#! /bin/sh
### BEGIN INIT INFO
# Provides:          rc.local
# Required-Start:    $all
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:
# Short-Description: Run /etc/rc.local if it exist
### END INIT INFO

PATH=/sbin:/usr/sbin:/bin:/usr/bin

bash /etc/setupwifi.sh
iptables -A FORWARD -p udp -d 10.1.1.10 --in-interface wlan0-ap --dport %s -j ACCEPT
iptables -A POSTROUTING -t nat --out-interface wlan0 -p udp --dport %s -j MASQUERADE --to %s

do_start() {
	if [ -x /etc/rc.local ]; then
		echo -n "Running local boot scripts (/etc/rc.local)"
		/etc/rc.local
		[ $? = 0 ] && echo "." || echo "error"
		return $ES
	fi
}

case "$1" in
    start)
	do_start
        ;;
    restart|reload|force-reload)
        echo "Error: argument '$1' not supported" >&2
        exit 3
        ;;
    stop)
        ;;
    *)
        echo "Usage: $0 start|stop" >&2
        exit 3
        ;;
esac
"""
new_ssid = raw_input("What is the ssid of the swarm network: ")
new_password = raw_input("What is the passkey for the swarm network: ")
new_port = raw_input("What is the port you want your artoo to forward: ")

setupwifi = setupwifi % ("ssid=\""+new_ssid+"\"\npsk=\""+new_password+"\"")
rclocal = rclocal % (new_port,new_port,new_port)

print "Connect to the network of the solo you want to work on"

artoo = ssh.ssh_instance()
artoo.connect("10.1.1.1")
artoo.command_blind("echo '" + timeout + "' > /etc/timeout.sh")
artoo.command_blind("chmod +x /etc/timeout.sh")
artoo.command_blind("echo '" + setupwifi + "' > /etc/setupwifi.sh")
artoo.command_blind("chmod +x /etc/setupwifi.sh")
artoo.command_blind("echo '" + rclocal + "' > /etc/rc5.d/S99rc.local")
artoo.command_blind("chmod +x /etc/rc5.d/S99rc.local")
print "Rebooting"
artoo.command_blind("reboot")
