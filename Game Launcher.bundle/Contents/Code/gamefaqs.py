# -*- coding: utf-8 -*-

# Plex Game Launcher Plugin
# by Aequitas

import os,subprocess,re,unicodedata,urllib,difflib, urllib
from htmlentitydefs import name2codepoint

HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.73.11 (KHTML, like Gecko) Version/6.1.1 Safari/537.73.11', 'referer' : 'http://google.com'}

Capabilities = ["title", "description", "developer", "publisher", "year", "genre", "url_boxart"]

BASE_URL = "http://www.gamefaqs.com"
TITLE_URL = BASE_URL + "/search/index.html?platform=%s&%s"

####################################################################################################
def search(fileTitle, console, gameParams=None, fileCRC=None, fuzzy=None, rerun=None):

	# Since we get here, we didn't find an exact match. Rerun but this time with a probabilty match
	if (rerun == None and fuzzy != None):
		return search(fileTitle, console, gameParams, None, fuzzy, True)

	Log("DEBUG: GameFaqs: searching for: " + fileTitle )

	grabbed = {}
	platform = translatePlatform(console)
	if (platform == ""):
		Log("WARING: Grabber does not support: " + console)
		return gameParams

	try:
		pagecontent = HTML.ElementFromURL( TITLE_URL % (0, urllib.urlencode({ 'game' : stripReleaseInfo(fileTitle)}) ), encoding='iso-8859-1', headers=HTTP_HEADERS )
	except Ex.HTTPError, e:
		Log('ERROR: Received http error code: ' + str(e.code) + ' from GameFaqs ABORTING')
		return gameParams
	except:
		Log('ERROR: GameFaqs is unavailable')
		return gameParams

	for link in pagecontent.xpath("//td[@class='rtitle']/a"):

		gamelink = link.xpath("@href")[0]
		gamesystem = gamelink.split('/')
		gamesystem = gamesystem[1]
		gameurl = BASE_URL+gamelink
		grabbed['title'] = transformChars(link.xpath("text()")[0])

		if ( compareReleaseNames(grabbed['title'], fileTitle, rerun, fuzzy) and (platform == gamesystem.lower()) ):

			searchpagecontent = HTML.ElementFromURL( gameurl, encoding='iso-8859-1', headers=HTTP_HEADERS )

			try:
				grabbed['description'] = transformChars(searchpagecontent.xpath("//div[@class='body game_desc']/div[@class='desc']/text()")[0])
			except:
				pass

			releasepagecontent = HTML.ElementFromURL( gameurl + '/data', encoding='iso-8859-1', headers=HTTP_HEADERS )

			try:
				grabbed['genre'] = transformChars(releasepagecontent.xpath("//dl[dt]/dd/text()")[0])
			except:
				pass

			try:
				grabbed['publisher'] = transformChars(releasepagecontent.xpath("//dl[dt]/dd/a/text()")[0])
			except:
				pass

			try:
				year = transformChars(releasepagecontent.xpath("//td[@class='cdate']/text()")[0])
				grabber['year'] = re.search('\d{4}', str(year)).group(0)
			except:
				pass

			if ('url_boxart' not in gameParams):
				mainpage = None
				if ('url_boxart' not in gameParams):
					mainpage = HTML.ElementFromURL( gameurl + "/images" )

					try:
						pageboxurl = mainpage.xpath("//div[div[@class='region']/text()[contains(.,'US') or contains(.,'EU')]]/a/@href")[0]
						pageboxcontent = HTML.ElementFromURL( BASE_URL + pageboxurl )
						grabbed['url_boxart'] = pageboxcontent.xpath("//div[@class='pod game_imgs']//a/@href[contains(.,'front')]")[0]
					except:
						pass

				#if ('url_screen' not in gameParams):
				#	if (mainpage == None):
				#		mainpage = HTML.ElementFromURL( gameurl + "/images" )
				#	try:
				#		pagescreenurl = mainpage.xpath("//td[@class='thumb']/a/@href[contains(.,'screen-1')]")[0]
				#		pagescreencontent = HTML.ElementFromURL( BASE_URL + pagescreenurl )
				#		grabbed['url_screen'] = pagescreencontent.xpath("//div[@class='img']/a/img[@class='full_boxshot']/../@href")[0]
				#	except:
				#		pass

			grabbed['scanned'] = 1
			return checkMissingInfo(gameParams, grabbed)

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
	platform = SYSTEMS_LIST[console.lower()][2]
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
