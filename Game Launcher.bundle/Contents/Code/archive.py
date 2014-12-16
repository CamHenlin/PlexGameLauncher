# -*- coding: utf-8 -*-

# Plex Game Launcher Plugin
# by Aequitas

import os,subprocess,re,unicodedata,difflib,urllib, urllib
from htmlentitydefs import name2codepoint
from datetime import date

Capabilities = ["title", "description", "developer", "year", "genre", "url_boxart"]

API_KEY = "KG9PYHPCPRTHQLAA9KUN696ZXUHH3D0Z"
BASE_URL = "http://api.archive.vg/2.0"
SYSTEM_URL = BASE_URL + "/Archive.getSystems/%s/"
SEARCH_URL = BASE_URL + "/Archive.search/%s/%s"
GAMEID_URL = BASE_URL + "/Game.getInfoByID/%s/%s"
GAMECRC_URL = BASE_URL + "/Game.getInfoByCRC/%s/%s"

####################################################################################################
def search(fileTitle, console, gameParams=None, fileCRC=None, fuzzy=None, rerun=None):

	# Since we get here, we didn't find an exact match. Rerun but this time with a probabilty match
	if (rerun == None and fuzzy != None):
		return search(fileTitle, console, gameParams, None, fuzzy, True)

	Log("DEBUG: Archive.vg: searching for: " + fileTitle )

	platform = translatePlatform(console)
	if (platform == ""):
		Log("WARING: Grabber does not support: " + console)
		return gameParams

	if (fileCRC and rerun == None):
		try:
			grabbed = getTitleByCRC(fileCRC)
			Log('CRC found, we are taking it')
			return checkMissingInfo(gameParams, grabbed)
		except:
			Log('DEBUG: CRC hash not found')
			pass

	titlesList = getTitleList(fileTitle)
	for id in titlesList:

		if ( ( compareReleaseNames(titlesList[id]['title'], fileTitle, rerun, fuzzy) ) and ( platform == titlesList[id]['platform'] ) ):

			grabbed = getReleaseInfo(id)
			return checkMissingInfo(gameParams, grabbed)

	return gameParams

####################################################################################################
def getTitleByCRC(fileCRC):
	pageCRC = XML.ElementFromURL( GAMECRC_URL % (API_KEY, fileCRC), encoding="UTF-8" ).xpath('//games/game')
	grabbed = getReleaseInfo(None, pageCRC[0])
	return grabbed

####################################################################################################
def getTitleList(fileTitle):
	titlesList = {}
	searchTitle = stripReleaseInfo(fileTitle)
	pageGames = XML.ElementFromURL( SEARCH_URL % (API_KEY, urllib.quote(searchTitle) ), encoding="UTF-8" ).xpath('//games/game')
	for game in pageGames:
		titlesList[game.find('id').text] = {}
		titlesList[game.find('id').text]['title'] = game.find('title').text
		titlesList[game.find('id').text]['platform'] = game.find('system').text
	return titlesList

####################################################################################################
def getReleaseInfo(titleID, page=None):

	if (page == None):
		page = XML.ElementFromURL( GAMEID_URL % ( API_KEY, titleID ), encoding="UTF-8" ).xpath('//games/game')[0]

	grabbed = {}
	grabbed['scanned'] = 1

	name = page.find('title')
	grabbed['title'] = (transformChars(name.text) if (name != "") else None)
	description = page.find('description')
	if (description.text != None):
		grabbed['description'] = (transformChars(description.text) if (description != "") else None)
	genre = page.find('genre')
	if (genre.text != None):
		grabbed['genre'] = (transformChars(genre.text) if (genre != "") else None)
	developer = page.find('developer')
	if (developer.text != None):
		grabbed['developer'] = (transformChars(developer.text) if (developer != "") else None)
	thumb = page.find('box_front')
	if (thumb.text != None):
		grabbed['url_boxart'] = (thumb.text if (thumb != "") else None)

	releases = page.xpath('//releases/release')
	for release in releases:

		try:
			if (release.find('country').text == 'US' or release.find('country').text == 'EU' and release.find('title').text == grabbed['title'] ):
				grabbed['year'] = release.find('date').text[:4]
		except:
			pass

	return grabbed

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
def translatePlatform(console):
	SYSTEMS_LIST = JSON.ObjectFromString( Resource.Load('json/grabbers.json') )
	platform = SYSTEMS_LIST[console.lower()][0]
	return platform

####################################################################################################
def stripReleaseInfo(name):
	name = name.split('[')[0].split('(')[0].rstrip()	# Strip release info from title
	name = re.findall("(\w+)", name, re.I)				# Remove all non-alphanumeric characters
	name = " ".join(name)								# Glue the parts back together
	name = name.replace('_',' ').strip()				# Replace any remaining underscores
	return name

####################################################################################################
def compareReleaseNames(release, game, rerun, fuzzy):
	gameTransformed  = stripCharsRomname(release)
	releaseTransformed = stripCharsRomname(game)
	if (rerun):
		result = difflib.SequenceMatcher(None, stripCharsRomname(release), stripCharsRomname(game)).ratio()
		if (result > float(fuzzy) / float(100)):
			Log('DEBUG: Found fuzzy match above our threshold: ' + str(fuzzy) + ' at: ' + str(round(result * 100,1)) + '% for title: ' + release)
			return True
		else:
			return False
	else:
		return gameTransformed == releaseTransformed

####################################################################################################
def stripCharsRomname(name):
	name = name.lower()
	name = name.split('[')[0].split('(')[0].split(u'\xa9')[0].rstrip()
	name = transformChars(name)						# encode in utf-8 for storage
	name = strip_accents(name)						# Transform accented letters for name matching
	name = name.replace('the','')
	name = name.replace('and',' ')
	name = re.findall("(\w+)", name, re.I)			# remove all non-alphanumeric characters
	name = os.linesep.join(name)
	name = name.replace("\n","")					# remove any remaining linebreaks left in the string
	name = name.replace("\r\n","")
	name = name.replace('_','')
	name = name.strip()
	return name

####################################################################################################
def strip_accents(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')

####################################################################################################
def transformChars(s):
	s = htmlentitydecode(s)
	s = s.decode('utf-8')
	return s

####################################################################################################
def htmlentitydecode(s):
    return re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)

####################################################################################################
def Thumb(url):
	try:
		data = HTTP.Request(url, cacheTime = CACHE_1MONTH).content
		return DataObject(data, 'image/jpeg')
	except:
		return Redirect(R(ICON))
