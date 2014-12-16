#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}
console=${args[2]}

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false" 

ext=${romname##*.}
ext=$(echo ${ext} | tr '[:upper:]' '[:lower:]');

cd "$emupath"MESS
cp "_backupconfig/default.cfg" "cfg/"

if [ "$console" = "atari 7800" ]; then
	./mess64 a7800 -cart "$romname"
elif [ "$console" = "atari 5200" ]; then
	./mess64 a5200 -cart "$romname"
elif [ "$console" = "atari 2600" ]; then
	./mess64 a2600 -cart "$romname"
elif [ "$console" = "commodore 64" ]; then
	echo $ext
	if [ "${ext}" = "tap" ] || [ "${ext}" = "wav" ]; then
		./mess64 c64cp -cass "$romname"
	elif [ "${ext}" = "d64" ] || [ "${ext}" = "g64" ]; then
		./mess64 c64cp -flop1 "$romname"
	elif [ "${ext}" = "crt" ]; then
		./mess64 c64cp -cart1 "$romname"
	elif [ "${ext}" = "prg" ]; then
		./mess64 c64cp -quick "$romname"
	else
		echo "Unsupported commodore 64 image"
	fi
elif [ "$console" = "sega cd" ]; then
	./mess64 segacd -cdrm "$romname"
elif [ "$console" = "sega 32x" ]; then
	./mess64 32x -cart "$romname"
elif [ "$console" = "sega dreamcast" ]; then
	./mess64 dc -cdrm "$romname"
elif [ "$console" = "sega genesis" ]; then
	./mess64 genesis -cart "$romname"
elif [ "$console" = "sega master system" ]; then
	./mess64 sms -cart "$romname"
elif [ "$console" = "sega saturn" ]; then
	./mess64 saturn -cart "$romname"
elif [ "$console" = "sega sg-1000" ]; then
	./mess64 sg1000 -cart "$romname"
elif [ "$console" = "sega game gear" ]; then
	./mess64 gamegear -cart "$romname"
elif [ "$console" = "nec turbografx-16" ]; then
	./mess64 pce -cart "$romname"
elif [ "$console" = "nec supergrafx" ]; then
	./mess64 sgx -cart "$romname"
elif [ "$console" = "nintendo game boy" ]; then
	./mess64 gameboy -cart "$romname"
elif [ "$console" = "nintendo game boy color" ]; then
	./mess64 gbc -cart "$romname"
elif [ "$console" = "nintendo game boy advance" ]; then
	./mess64 gba -cart "$romname"
elif [ "$console" = "nintendo entertainment system" ]; then
	./mess64 nes -cart "$romname"
elif [ "$console" = "super nintendo entertainment system" ]; then
	./mess64 snes -cart "$romname"
elif [ "$console" = "nintendo 64" ]; then
	./mess64 n64 -cart "$romname"
elif [ "$console" = "atari lynx" ]; then
	./mess64 lynx -cart "$romname"
elif [ "$console" = "bandai wonderswan" ]; then
	./mess64 wswan -cart "$romname"
elif [ "$console" = "bandai wonderswan color" ]; then
	./mess64 wscolor -cart "$romname"
elif [ "$console" = "coleco colecovision" ]; then
	./mess64 coleco -cart "$romname"
else
	echo "Unsupported system detected: $console"
fi

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
