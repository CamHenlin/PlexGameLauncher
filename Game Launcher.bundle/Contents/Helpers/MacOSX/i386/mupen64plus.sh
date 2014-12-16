#!/bin/bash

args=("$@")
romname=${args[0]}
emupath=${args[1]}
driver=${args[4]}
tempdir=$TMPDIR

if [ "$driver" == "" ]; then driver="rice"; fi

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to false" 

cd "$emupath"Mupen64plus
./mupen64plus.app/Contents/MacOS/mupen64plus --corelib ./mupen64plus.app/Contents/MacOS/libmupen64plus.dylib --resolution 1440x900 --fullscreen --osd --plugindir ./mupen64plus.app/Contents/MacOS --gfx  mupen64plus-video-"$driver" "$romname"

/usr/bin/osascript -e "tell application \"System Events\" to set visible of process \"Plex\" to true"
/usr/bin/osascript -e "tell application \"Plex\" to activate"
