#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false"

open -a "$emupath"OpenEmu/OpenEmu.app "$romname"

/usr/bin/osascript -e '
tell application "OpenEmu" to activate
	tell application "System Events"
	keystroke "f" using command down
end tell'

sleep 1

while [ `ps -ef | grep OpenEmu | grep -v openemu.sh | grep -v OpenEmuHelperApp | grep -v grep | awk '{print $2}' | wc -l` = 1 ]
	do sleep 1
done

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
