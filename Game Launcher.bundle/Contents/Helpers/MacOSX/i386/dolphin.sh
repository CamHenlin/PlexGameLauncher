#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false" 

open -a "$emupath"Dolphin"/"Dolphin.app "$romname"

sleep 3

while [ `ps -ef | grep Dolphin | grep -v dolphin.sh | grep -v grep | awk '{print $2}' | wc -l` = 1 ]
	do sleep 1
done

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
