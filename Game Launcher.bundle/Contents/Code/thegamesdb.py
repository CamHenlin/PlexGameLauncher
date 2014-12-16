# -*- coding: utf-8 -*-

# Plex Game Launcher Plugin
# by Aequitas

import os,subprocess,re,unicodedata,difflib, urllib
from htmlentitydefs import name2codepoint

Capabilities = ["title", "description", "developer", "publisher", "year", "genre", "players", "url_trailer", "url_boxart", "url_fanart", "url_banner", "url_screen"]

BASE_URL = "http://thegamesdb.net/api"
TITLE_URL = BASE_URL + "/GetGamesList.php?name=%s"
GAME_URL = BASE_URL + "/GetGame.php?id=%s"
IMG_URL = "http://thegamesdb.net/banners/"

####################################################################################################
def search(fileTitle, console, gameParams=None, fileCRC=None, fuzzy=None, rerun=None):

	if (rerun == None and fuzzy != None):
		return search(fileTitle, console, gameParams, None, fuzzy, True)

	Log("DEBUG: TheGamesDB: searching for: " + fileTitle )

	grabbed = {}
	platform = translatePlatform(console)
	if (platform == ""):
		Log("WARING: Grabber does not support: " + console)
		return gameParams

	pagecontent = HTML.ElementFromURL( TITLE_URL % (stripReleaseInfo(fileTitle)) )
	page = HTML.StringFromElement(pagecontent)

	games = re.findall("<Game><id>(.*?)</id><GameTitle>(.*?)</GameTitle>(.*?)<Platform>(.*?)</Platform></Game>", page.replace('\r\n', '').replace('\n', '') )
	for item in games:

		gameUrl = GAME_URL % item[0]
		gameTitle = unescape(item[1])
		gameSys = item[3]

		if ( compareReleaseNames(gameTitle, fileTitle, rerun, fuzzy) and (platform == gameSys.lower()) ):

			pagecontent = HTML.ElementFromURL( gameUrl ).replace('\r\n', '').replace('\n', '')
			page = HTML.StringFromElement(pagecontent)

			grabbed['title'] = gameTitle

			gameGenre = ' / '.join(re.findall('<genre>(.*?)</genre>', page))
			if gameGenre:
				grabbed['genre'] = unescape(gameGenre)

			gameDate = re.findall('<ReleaseDate>(.*?)</ReleaseDate>', page)
			if gameDate:
				grabbed['year'] = gameDate[0][-4:]

			gameDev = re.findall('<Developer>(.*?)</Developer>', page)
			if gameDev:
				grabbed['developer'] = unescape(gameDev[0])

			gamePubl = re.findall('<Publisher>(.*?)</Publisher>', page)
			if gamePubl:
				grabbed['publisher'] = unescape(gamePubl[0])

			gameDescr = re.findall('<Overview>(.*?)</Overview>', page)
			if gameDescr:
				grabbed['description'] = unescape(gameDescr[0])

			gamePlayer = re.findall('<Players>.*?([0-9]+).*?</Players>', page)
			if gamePlayer:
				grabbed['players'] = unescape(gamePlayer[0])

			gameTrailer = re.findall('<Youtube>(.*?)</Youtube>', page)
			if gameTrailer:
				grabbed['url_trailer'] = unescape(gameTrailer[0])

			gameThumb = re.findall('<boxart side="front" (.*?)>boxart/(.*?)</boxart>', page)
			if gameThumb:
				grabbed['url_boxart'] = IMG_URL + "boxart/" + gameThumb[0][1]

			gameFanart = re.findall('<original (.*?)">fanart/(.*?)</original>', page)
			if gameFanart:
				grabbed['url_fanart'] = IMG_URL + "fanart/" + gameFanart[0][1]

			gameBanner = re.findall('<banner (.*?)">graphical/(.*?)</banner>', page)
			if gameBanner:
				grabbed['url_banner'] = IMG_URL + "graphical/" + gameBanner[0][1]

			grabbed['scanned'] = 1

			gameParams = checkMissingInfo(gameParams, grabbed)

			return gameParams

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
def translatePlatform(console):
	SYSTEMS_LIST = JSON.ObjectFromString( Resource.Load('json/grabbers.json') )
	platform = SYSTEMS_LIST[console.lower()][3]
	return platform

####################################################################################################
def stripReleaseInfo(name):
	name = name.split('[')[0].split('(')[0].rstrip()
	return re.sub('_', ' ', name)

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
	name = transformChars(name)						# strip out ISO-something chars before we start alphanumeric matching
	name = strip_accents(name)						# transform accented letters for name matching
	name = name.replace('the','')
	name = name.replace('and',' ')
	name = re.findall("(\w+)", name, re.I)					# remove all non-alphanumeric characters
	name = os.linesep.join(name)
	name = name.replace("\n","")						# remove any remaining linebreaks left in the string
	name = name.replace("\r\n","")
	name = name.replace('_','')
	name = name.strip()
	return name

####################################################################################################
def transformChars(name):
	name = name.replace('&egrave;','')
	name = name.replace('&agrave;','')
	name = name.replace('&ugrave;','')
	name = name.replace('&ograve;','')
	name = name.replace('&igrave;','')
	name = name.replace('&eacute;','')
	name = name.replace('&aacute;','')
	name = name.replace('&uacute;','')
	name = name.replace('&oacute;','')
	name = name.replace('&iacute;','')
	name = name.replace('&quot;','\'')
	return name

####################################################################################################
def strip_accents(s):
	#return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
	return s

####################################################################################################
def unescape(s):
    s = s.replace('<br />',' ')
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&amp;", "&")
    s = s.replace("&#039;","'")
    s = s.replace('<br />',' ')
    s = s.replace('&quot;','"')
    s = s.replace('&nbsp;',' ')
    s = s.replace(u'&#x26;','&')
    s = s.replace(u'&#x27;',"'")
    return s

# def unescape(s):
#     #"unescape HTML code refs; c.f. http://wiki.python.org/moin/EscapingHtml"
#     return re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)

