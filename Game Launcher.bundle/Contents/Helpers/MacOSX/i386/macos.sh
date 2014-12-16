#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false"

open -a "${romname}" &

filename=${romname##*/}
extension=${filename##*.}
appname=${filename%.*}

sleep 2

if [ "${appname}" = "Mari0" ]; then
	
	# set application active
	/usr/bin/osascript -e "tell application \"${appname}\" to activate"
	
elif  [ "${appname}" = "test" ]; then
	
	# set application active and force fullscreen with coammand + f
		/usr/bin/osascript -e "
	tell application \"${appname}\" to activate
	delay 1
	tell application \"System Events\"
		keystroke \"f\" using command down
	end tell"
	
else
	
	# set application active and force fullscreen with option + enter
	/usr/bin/osascript -e "
tell application \"${appname}\" to activate
delay 1
tell application \"System Events\"
	key code 36 using option down
end tell"

fi

sleep 3

while [ `ps -ef | grep "${filename}" | grep -v grep | grep -v macos.sh | awk '{print $1}' | wc -l` = 1 ]
	do sleep 1
done

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
