#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false" 

if [ "${romname##*.}" = "ogv" ]; then
	# laserdisc
	# machine="Pioneer_PX-V60"
	machine="Pioneer_PX-7"
else
	# msx2
	machine="Philips_NMS_8245"
	#machine="Sony_HB-F900"
fi

if [ "${romname##*.}" = "ogv" ]; then
	type="-laserdisc"
elif [ "${romname##*.}" = "dsk" ]; then
	type="-diska"
else
	type="-cart"
fi

cd $emupath"OpenMSX/openMSX.app/Contents/MacOS"
./openmsx -machine "${machine}" ${type} "${romname}"

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
