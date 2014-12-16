#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false" 
# /usr/bin/osascript -e "tell application \"Plex\" to quit" 

open -a "$emupath"Snes9x/Snes9x.app "$romname"


sleep 3

while [ `ps -ef | grep Snes9x  | grep -v snes9x.sh | grep -v grep | awk '{print $2}' | wc -l` = 1 ]
	do sleep 1
done

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"

