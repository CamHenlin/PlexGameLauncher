#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false" 

filename=${romname##*/}
name=${filename%.*}

cd ${emupath}"Daphne/Daphne.app/Contents/MacOS"
./Daphne ${name} vldp -fullscreen -x 800 -y 600 -opengl -useoverlaysb 2 -fastboot -framefile "${romname}" -homedir ${emupath}"Daphne" &

sleep 3

while [ `ps -ef | grep Daphne | grep -v daphne.sh | grep -v grep | awk '{print $2}' | wc -l` = 1 ]
	do sleep 1
done

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
