#!/bin/sh

args=("$@")
gamename=${args[0]}				# full game name
emupath=${args[1]}				# emulator path
players=${args[2]}				# number of players
buttonlocation=${args[3]}		# controller button label locations ( list )
buttonlabels=${args[4]}			# controller button label text ( list )
controllername=${args[5]}		# controller name
controllerbuttons=${args[6]}	# controller button names used for the overlays ( list )
unboundbuttons=${args[7]}		# unbound mame buttons ( list )
description=${args[8]}			# description

cachedir=${emupath}"CPanel/cache/"
imagedir=${emupath}"CPanel/images/"
convertdir=${emupath}"CPanel/tool/bin/"

export MAGICK_HOME="${emupath}CPanel/tool"
export PATH="$MAGICK_HOME/bin:$PATH"
export DYLD_LIBRARY_PATH="$MAGICK_HOME/lib"

cd ${emupath}"CPanel"

function createTextMap() {
	labelname=${1}
	# Test to see if the image already exists, if so just skip this step to speed up
	if [ ! -f "${cachedir}${labelname}.png" ]; then
		lname=""
		for (( i = 0 ; i < ${#labelname} ; i++ ))
		do
			char=${labelname:$i:1}
			lname+=" "${imagedir}"letters/"${char}".png "
		done
		${convertdir}convert ${lname} "+append" "${cachedir}${labelname}.png"
	fi
}

IFS=';' read -ra unboundbuttonsArr <<< "$unboundbuttons"
IFS=';' read -ra controllerbuttonsArr <<< "$controllerbuttons"
IFS=';' read -ra buttonlabelsArr <<< "$buttonlabels"
IFS=';' read -ra buttonlocationArr <<< "$buttonlocation"
IFS=';' read -ra descriptionArr <<< "$description"

#count=${#buttonlabelsArr[@]}

convertcom=" -page 1920x1080 -background none"

# FIXME: seems imagemagick convert doesn't like starting off with a jpg ... this can be removed when it's fixed
convertcom+=" -page +0+0 ${imagedir}blank.png"

convertcom+=" -page +0+0 ${imagedir}template/background.jpg"
convertcom+=" -page +0+0 ${imagedir}controllers/${controllername}.png"

# insert the pointers for the labels
for labelliner in ${controllerbuttonsArr[@]}; do
	convertcom+=" -page +0+0 ${imagedir}template/${labelliner}.png"
done

# insert all the labels
n=0
for label in ${buttonlabelsArr[@]}; do
    createTextMap $label
	convertcom+=" -page ${buttonlocationArr[$n]} ${cachedir}${label}.png"
	((n++))
done

# insert the game title into the picture
if [ $gamename != "" ]; then
	createTextMap $gamename
	convertcom+=" -page +50+50 ${cachedir}${gamename}.png"
fi

# insert the number of players supported
if [ $players != "" ]; then
	createTextMap "players_-_$players"
	convertcom+=" -page +50+80 ${cachedir}players_-_$players.png"
fi

if [ "${unboundbuttons}" != "" ]; then
	y=170; unboundcom=""
	# insert the pointers for the labels
	for unbound in ${unboundbuttonsArr[@]}; do
	    createTextMap $unbound
		unboundcom+=" -page +50+${y} ${cachedir}${unbound}.png"
		((y=y+30))
	done

    createTextMap "Unbound_controls_found"
	convertcom+=" -page +50+140 ${cachedir}Unbound_controls_found.png"
	convertcom+=${unboundcom}
fi


if [ "${descriptionArr}" != "" ]; then
	y=940
	for description in ${descriptionArr[@]}; do
		createTextMap $description
		convertcom+=" -page +50+${y} ${cachedir}${description}.png"
		((y=y+30))
	done
fi

convertcom+=" -flatten ${cachedir}controllermap.jpg"

${convertdir}convert ${convertcom}

if [ ! -f "${cachedir}controllermap.jpg" ]; then
	echo "-\n\n################################\n\nUnable to create controllermap, convert binary probably wrong read more about it here: \nhttp://forums.plexapp.com/index.php/topic/36540-game-launcher-revised/page__view__findpost__p__238799\n\n################################"
fi

open -a "${emupath}CPanel/fullscreen/fullScr.app" "${cachedir}controllermap.jpg"

sleep 1

while [ `ps -ef | grep fullScr | grep -v grep | awk '{print $2}' | wc -l` = 1 ]
	do sleep 1
done

