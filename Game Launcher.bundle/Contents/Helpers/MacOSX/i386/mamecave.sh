#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false" 

cd $emupath"MAME"
cp "_backupconfig/default.cfg" "cfg/"
./mame64cave -rompath "./roms;${romname%/*};${basedir}/CHD;${basedir}/Ignore" "${romname##*/}"

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
