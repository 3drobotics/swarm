#!/bin/bash


# kill process names that might stil
# be running from last time
pkill gazebo
pkill mainapp
jmavsim_pid=`jps | grep Simulator | cut -d" " -f1`
if [ -n "$jmavsim_pid" ]
then
	kill $jmavsim_pid
fi
