#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false" 

open -a "$emupath"Fuse/Fuse.app "$romname"

/usr/bin/osascript -e 'tell application "System Events"
	tell process "Fuse"
		set windowTitle to title of window 1 
		click menu item windowTitle of menu 1 of menu bar item "Window" of menu bar 1
	end tell
	keystroke "f" using command down
end tell'

sleep 2

while [ `ps -ef | grep Fuse | grep -v fuse.sh | grep -v grep | awk '{print $2}' | wc -l` = 1 ]
	do sleep 1
done

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
