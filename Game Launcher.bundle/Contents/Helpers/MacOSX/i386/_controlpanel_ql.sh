#!/bin/sh

# Script to dynamicly create a overlayed image with controllers and buttons for previewing the controlls for mame

args=("$@")
rompath=${args[0]}
emupath=${args[1]}
players=${args[2]}
control=${args[3]}
buttons=${args[4]}

cachedir=${emupath}"CPanel/cache/"
cachefile=${cachedir}${rompath%.*}".png"

cpanel="back-default.png"

cd ${emupath}"CPanel"


function createTextMap() {
	buttonname=${1}
	cachedir=${2}
	bname=""
	for (( i = 0 ; i < ${#buttonname} ; i++ ))
	do
		char=${buttonname:$i:1}
		bname+=" images/letters/"${char}".png "
	done
	./convert ${bname} +append ${cachedir}"strings/"${buttonname}.png
}

# end command for convert
buttoncol=("orange" "blue" "purple" "yellow" "orange" "blue" "purple" "yellow")
buttonpos=("+500+290" "+600+270" "+700+250" "+800+255" "+500+390" "+600+370" "+700+350" "+800+355")
stringpos=("+470+260" "+570+240" "+665+220" "+805+225" "+470+360" "+570+340" "+665+320" "+805+325")

concom=""	
IFS=';' read -ra buttonArr <<< "$buttons"
count=${#buttonArr[@]}
n=0
for button in ${buttonArr[@]}; do
    createTextMap $button ${cachedir}
	concom+=" -page ${buttonpos[$n]} images/but-${buttoncol[$n]}.png -page ${stringpos[$n]} cache/strings/${button}.png"
	if [ "${count}" -gt "6" ]; then
		((n++))
	elif [ "${count}" -gt "4" ]; then
		if [ "${n}" == "2" ]; then n=3; fi; ((n++))
	else
		if [ "${n}" == "1" ]; then n=3; fi; ((n++))
	fi	
done

if [ "${control}" != "" ]; then
convertcom=" -page 1024x768+200+230 images/${control}.png"
convertcom+=" -page +278+280 images/ctrl-js-red.png"
convertcom+=${concom}
convertcom+=" -page +0+0 images/back-default.png"
convertcom+=" -background none -compose DstOver -flatten ${cachedir}games/test.png"
./convert ${convertcom}
#elif [ "${control}" == "trackball"]; then
#elif [ "${control}" == "dial"]; then			#spinner
#elif [ "${control}" == "paddle"]; then			#wheel
#elif [ "${control}" == "other"]; then			#mahjong
#else
fi				


#doublejoy8way			= controls through 2 8 way sticks ( move and aim for example )
#stick					= 49way

#qlmanage -p "$@" &>/dev/null &
qlmanage -p "${cachedir}games/test.png" &>/dev/null
#QL_PID=$!

#sleep 1

#echo "Press any key to return"
#read -s -n 1

#kill $QL_PID



