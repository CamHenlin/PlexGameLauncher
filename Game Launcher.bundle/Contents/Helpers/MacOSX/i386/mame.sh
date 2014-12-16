#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false" 

romsdir=${romname%/*}
basedir=${romsdir%/*}

cd $emupath"MAME"
cp "_backupconfig/default.cfg" "cfg/"
./mame64plain -rompath "./roms;${romname%/*};${basedir}/CHD;${basedir}/Ignore" "${romname##*/}"

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
