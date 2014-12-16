# -*- coding: utf-8 -*-

# Plex Game Launcher Plugin
# by Aequitas

import os,subprocess,re,unicodedata,difflib, urllib
from htmlentitydefs import name2codepoint

Capabilities = ["title", "description", "developer", "publisher", "year", "genre", "url_boxart"]
# Even though giantbomb lists screenshots, they are simply a low quality boxart image in 95% of the time so we don't use it

API_KEY = "9d8ec266a4043716015d4be2857d62c89b69f462"
SYSTEM_URL = "http://api.giantbomb.com/platforms/?api_key=%s&field_list=name,abbreviation,id&format=json"
TITLE_URL = "http://api.giantbomb.com/search/?api_key=%s&query=%s&resources=game&field_list=name,id&format=json"
RELEASE_URL = "http://api.giantbomb.com/game/%s/?api_key=%s&field_list=name,deck,genres,releases,image,publishers,developers&format=json"
PLATFORM_URL = "http://api.giantbomb.com/release/%s/?api_key=%s&field_list=platform,image,release_date,publishers,developers,region&format=json"
REGION_IDS = [1, 2] # 1 = US, 2 = UK, we accept both to increase our chances of a better hit

####################################################################################################
def search(fileTitle, console, gameParams=None, fileCRC=None, fuzzy=None, rerun=None):

	# Since we get here, we didn't find an exact match. Rerun but this time with a probabilty match
	if (rerun == None and fuzzy != None and len(gameParams) == 0):
		return search(fileTitle, console, gameParams, None, fuzzy, True)

	Log("DEBUG: GiantBomb: searching for: " + fileTitle )

	grabbed = {}
	platform = translatePlatform(console)
	if (platform == ""):
		Log("WARING: Grabber does not support: " + console)
		return gameParams

	# strip possible release info out of the filename
	searchTitle = stripReleaseInfo(fileTitle)
	# Search GiantBomb for possible game titles
	titleResults = JSON.ObjectFromURL( TITLE_URL % (API_KEY, String.Quote(searchTitle)), encoding = 'UTF-8' )
	for title in titleResults['results']:
		# See if we can find a match for the title we are searching
		if ( compareReleaseNames(title['name'], fileTitle, rerun, fuzzy) ):
			#Log('We found a match, jippie')
			# Search through all the releases we can find and see if there's a match
			releaseResults = JSON.ObjectFromURL( RELEASE_URL % (title['id'], API_KEY ), encoding = 'UTF-8' )
			if ( 'releases' not in releaseResults['results'] ):
				continue
				Log('################### None detected ######################')


			for release in releaseResults['results']['releases']:
				# perform a second match here to skip alternate titles
				if ( compareReleaseNames(release['name'], fileTitle, rerun, fuzzy) ):
					# We found atleast 1 match, grab the data we need

					grabbed['title'] = releaseResults['results']['name']
					grabbed['description'] = (releaseResults['results']['deck'] 					if (releaseResults['results']['deck']) else None)
					if ('genre' in releaseResults['results']): grabbed['genre'] = releaseResults['results']['genres'][0]['name']
					grabbed['developer'] = (releaseResults['results']['developers'][0]['name'] 		if (releaseResults['results']['developers']) else None)
					grabbed['publisher'] = (releaseResults['results']['publishers'][0]['name'] 		if (releaseResults['results']['publishers']) else None)

					grabbed['scanned'] = 1

					if ('url_boxart' not in gameParams or 'url_screen' not in gameParams or 'year' not in gameParams):
						# Grab platform specific information
						platformResult = JSON.ObjectFromURL( PLATFORM_URL  % (release['id'], API_KEY), encoding = 'UTF-8' )
						if ( (platformResult['results']['platform']['name'].lower() == platform) and (platformResult['results']['region']['id'] in REGION_IDS) ):
							grabbed['year'] = (platformResult['results']['release_date'].split('-')[0]		if (platformResult['results']['release_date']) else None)
							if (platformResult['results']['image']):
								grabbed['url_boxart'] = (platformResult['results']['image']['super_url'] 	if (platformResult['results']['image']['super_url']) else None)
							#grabbed['url_screen'] = (platformResult['results']['image']['screen_url'] 	if (platformResult['results']['image']['screen_url']) else None)

							return checkMissingInfo(gameParams, grabbed)

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
def translatePlatform(console):
	SYSTEMS_LIST = JSON.ObjectFromString( Resource.Load('json/grabbers.json') )
	platform = SYSTEMS_LIST[console.lower()][1]
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
