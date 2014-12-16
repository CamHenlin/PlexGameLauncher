# -*- coding: utf-8 -*-

# Plex Game Launcher Plugin
# by Aequitas

import os,subprocess,re,unicodedata,urllib,difflib, urllib
from htmlentitydefs import name2codepoint

Capabilities = ["title", "description", "developer", "publisher", "year", "genre", "url_screen"]

BASE_URL = "http://www.allgame.com"
SEARCH_URL = BASE_URL + "/search.php"
TITLE_URL = BASE_URL + "/game.php?id=%s"
SCREEN_URL = BASE_URL + "/game.php?id=%s&tab=screen"

####################################################################################################
def search(fileTitle, console, gameParams=None, fileCRC=None, fuzzy=None, rerun=None):

	# Since we get here, we didn't find an exact match. Rerun but this time with a probabilty match
	if (rerun == None and fuzzy != None):
		return search(fileTitle, console, gameParams, None, fuzzy, True)

	Log("DEBUG: AllGame: searching for: " + fileTitle )

	platform = translatePlatform(console)
	if (platform == ""):
		Log("WARING: Grabber does not support: " + console)
		return gameParams

	titlesList = getTitleList(fileTitle)
	for id in titlesList:

		if ( ( compareReleaseNames(titlesList[id]['title'], fileTitle, rerun, fuzzy) ) and ( int(platform) == int(titlesList[id]['platform']) ) ):

			grabbed = getReleaseInfo(id)
			return checkMissingInfo(gameParams, grabbed)

	return gameParams

####################################################################################################
def getTitleList(fileTitle):
	params = {'sql' : stripReleaseInfo(fileTitle), 'opt1': 81, 'encoding': 'UTF-8'}
	pagesearchcontent = HTML.ElementFromURL( SEARCH_URL, params )
	pagesearch = HTML.StringFromElement(pagesearchcontent)

	titlesList = {}
	gameID = re.findall('<a href="game.php\?id=(.*?)">(.*?)</a>', pagesearch)
	gamesys = re.findall('<a href="platform.php\?id=(.*?)">(.*?)</a>', pagesearch)
	for game, sys in zip(gameID,gamesys):
		titlesList[game[0]] = {}
		titlesList[game[0]]['title'] = game[1]
		titlesList[game[0]]['platform'] = sys[0]
	return titlesList

####################################################################################################
def getReleaseInfo(titleID):

	grabbed = {}
	pagetitlecontent = HTML.ElementFromURL( TITLE_URL % (titleID), encoding = 'UTF-8' )
	pagetitle = HTML.StringFromElement(pagetitlecontent)

	game_title = re.findall('<h3>Title</h3><p>(.*?)</p>', pagetitle)
	if game_title:
		grabbed["title"] = game_title[0]
	game_genre = ''.join(re.findall('<a href="genre.php[^>]*>(.*?)</a>', pagetitle))
	if game_genre:
		grabbed["genre"] = game_genre
	release_date = re.findall('<h3>Release Date</h3>[^>]*>(.*?)</p>', pagetitle)
	if release_date:
		grabbed["year"] = release_date[0][-4:]
	game_studio = re.findall('<h3>Developer</h3>[^>]*>(.*?)</p>', pagetitle)
	if game_studio:
		p = re.compile(r'<.*?>')
		gamestudio = p.sub('', game_studio[0])
		if gamestudio:
			grabbed["developer"] = gamestudio.rstrip()
	game_pub = re.findall('<h3>Publisher</h3>[^>]*>(.*?)</p>', pagetitle)
	if game_pub:
		p = re.compile(r'<.*?>')
		gamepub = p.sub('', game_pub[0])
		if gamepub:
			grabbed["publisher"] = gamepub.rstrip()
	plot = re.findall('<h2 class="title">(.*?)</p>(.*?)<p>(.*?)</p>', pagetitle, re.M | re.S)
	if plot:
		p = re.compile(r'<.*?>')
		grabbed["description"] = transformChars(p.sub('', plot[0][2]))

	url_screen = re.findall('(game.php\?id='+titleID+'\&tab=screen)', pagetitle)
	if url_screen:
		try:
			pagescreencontent = HTML.ElementFromURL( TITLE_URL % (titleID), encoding = 'UTF-8' )
			pagescreen = HTML.StringFromElement(pagesearchcontent)
			urlscreen = re.findall('<div id="screens">(.*?)<img src="(.*?)"', pagescreen, re.M | re.S)
			grabbed['url_screen'] = urlscreen[0][1]
		except:
			pass

	grabbed['scanned'] = 1

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
	platform = SYSTEMS_LIST[console.lower()][4]
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

