#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false"

open -a "$emupath"Pcsxr/PCSXR.app "$romname" &

/usr/bin/osascript -e "tell application \"PCSXR\" to activate"

sleep 2

while [ `ps -ef | grep PCSXR | grep -v pcsxr.sh | grep -v grep | awk '{print $2}' | wc -l` = 1 ]
	do sleep 1
done

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
