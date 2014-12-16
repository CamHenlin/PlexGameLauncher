#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}
console=${args[2]}


/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false"

cd "$emupath""Kega Fusion/Kega Fusion.app/Contents/MacOS"

if [ "$console" = "sega cd" ]; then
	./Kega\ Fusion "$romname" -scd -auto &
elif [ "$console" = "sega 32x" ]; then
	./Kega\ Fusion "$romname" -32x -auto &
elif [ "$console" = "sega genesis" ]; then
	./Kega\ Fusion "$romname" -gen -auto &
elif [ "$console" = "sega master system" ]; then
	./Kega\ Fusion "$romname" -sms -auto &
elif [ "$console" = "sega megacd" ]; then
	./Kega\ Fusion "$romname" -mcd -auto &
elif [ "$console" = "sega mega drive" ]; then
	./Kega\ Fusion "$romname" -md -auto &
else
	echo "Unsupported system"
fi

/usr/bin/osascript -e '
tell application "Kega Fusion" to activate
delay 1
tell application "System Events"
	key code 36 using option down
end tell'

sleep 1

while [ `ps -ef | grep Kega\ Fusion | grep -v grep | awk '{print $2}' | wc -l` = 1 ]
	do sleep 1
done

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
