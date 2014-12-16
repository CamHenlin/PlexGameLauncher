#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}

rompath=${romname%/*}
filename=${romname##*/}
gameid=${filename%.*}

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false"

"$emupath"ResidualVM/ResidualVM.app/Contents/MacOS/ResidualVM -p "$rompath" "$gameid"

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
