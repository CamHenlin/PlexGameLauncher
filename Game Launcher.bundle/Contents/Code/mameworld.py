# Plex Game Launcher Plugin
# by Nudgenudge <nudgenudge@gmail.com>

import os,subprocess,re

Capabilities = ["title", "description", "publisher", "year", "genre", "url_thumb"]

TITLE_URL = "http://maws.mameworld.info/maws/romset/%s"
THUMB_URL = "http://maws.mameworld.info/img/ps/titles/%s.png"

####################################################################################################
def search(fileTitle, console, gameParams=None):
	PMS.Log("DEBUG: MAWS: searching for: " + fileTitle)

	grabbed = {}

	page = XML.ElementFromURL( TITLE_URL % (gameID), isHTML=True)

	gameTitle = page.xpath("//td[text()='title']/../td[last()]/text()")
	grabbed['title'] = (stripReleaseInfo(gameTitle[0]) if (tempName) else fileTitle)

	grabbed['url_screen'] = THUMB_URL % (fileTitle)

	# Description
	gameDescr = ""
	tempDesc = page.xpath("//td[text()='history']/../td[last()]/text()")
	i = 0
	passedGameName = False
	while (i < len(tempDesc)):
		tempDescString = "%s" % (tempDesc[i])
		tempDescString = tempDescString.strip()
		if (tempDescString.find("- TECHNICAL -") != -1):
			break
		if (tempDescString != ""):
			if (not passedGameName):
				passedGameName = True
			else:
				gameDescr += tempDescString
				gameDescr += '\n\n'
		i += 1

	if (gameDescr):
		grabbed['description'] = gameDescr.strip()

	# Publisher
	gamePubl = page.xpath("//td[text()='manufacturer']/../td[last()]//text()")
	if (gamePubl):
		grabbed['publisher'] = gamePubl.group(1).strip()

	# Release date
	gameDate = page.xpath("//td[text()='year']/../td[last()]//text()")
	if (gameDate):
		game['year'] = gameDate.group(1).strip()

	# Genre
	gameGenre = page.xpath("//td[text()='genre']/../td[last()]//text()")
	if (gameGenre):
		grabbed['genre'] = gameGenre.group[0].strip()

	grabbed['scanned'] = 1

	gameParams = checkMissingInfo(gameParams, grabbed)
	return gameParams

####################################################################################################
# If current results are not complete, check if we have previous data we can append to
####################################################################################################
def checkMissingInfo(gameParams, grabbed):
	if (gameParams is not None):
		for key, value in grabbed.iteritems():
			if (key in gameParams):
				if (grabbed[key] != None):
					if (grabbed[key] != ""):
						if (gameParams[key] == None):
							gameParams[key] = grabbed[key]
			else:
				if (grabbed[key] != None):
					if (grabbed[key] != ""):
						gameParams[key] = grabbed[key]
		return gameParams
	return grabbed

####################################################################################################
def stripReleaseInfo(name):
	return 	name.split(u'(')[0].split(u'\xa9')[0].rstrip()

