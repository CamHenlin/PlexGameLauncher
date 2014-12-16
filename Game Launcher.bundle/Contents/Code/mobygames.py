# -*- coding: utf-8 -*-

# Plex Game Launcher Plugin
# by Aequitas

import os,subprocess,re,unicodedata,urllib,difflib, urllib
from htmlentitydefs import name2codepoint
from HTMLParser import HTMLParser

HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.73.11 (KHTML, like Gecko) Version/6.1.1 Safari/537.73.11', 'referer' : 'http://google.com'}

Capabilities = ["title", "description", "url_boxart", "publisher", "developer", "year", "genre"]

BASE_URL = "http://www.mobygames.com"
TITLE_URL = BASE_URL + "/search/quick?p=%s&q=%s&search=Go&sFilter=1&sG=on"

####################################################################################################
def search(fileTitle, console, gameParams=None, fileCRC=None, fuzzy=None, rerun=None):

	# Since we get here, we didn't find an exact match. Rerun but this time with a probabilty match
	if (rerun == None and fuzzy != None):
		return search(fileTitle, console, gameParams, None, fuzzy, True)

	Log("DEBUG: MobyGames: searching for: " + fileTitle )

	grabbed = {}
	platform = translatePlatform(console)
	if (platform == ""):
		Log("WARING: Grabber does not support: " + console)
		return gameParams

	try:
		pagecontent = HTML.ElementFromURL( TITLE_URL % (platform, urllib.urlencode({ 'game' : stripReleaseInfo(fileTitle)}) ), encoding='utf-8', headers=HTTP_HEADERS )
	except Ex.HTTPError, e:
		Log('ERROR: Received http error code: ' + str(e.code) + ' from mobygames ABORTING')
		return gameParams
	except:
		Log('ERROR: mobygames is unavailable')
		return gameParams

	for link in pagecontent.xpath("//div[@class='searchTitle']/a"):

		gamelink = link.xpath("@href")[0]
		gameurl = BASE_URL+gamelink
		grabbed['title'] = transformChars(link.xpath("text()")[0])

		if ( compareReleaseNames(grabbed['title'], fileTitle, rerun, fuzzy) ):

			pagecontent = HTML.ElementFromURL( gameurl, encoding='utf-8', headers=HTTP_HEADERS )
			page = HTML.StringFromElement(pagecontent)

			try:
				# Description
				pattern = re.compile('<h2>Description</h2>(.+?)<div class="sideBarLinks">\[<a href="/contrib', re.DOTALL|re.I)
				tempDescription = pattern.search(page)

				gameDescr = tempDescription.group(1).replace('<br>','').strip()
				gameDescr = os.linesep.join([s for s in gameDescr.splitlines() if s])
				gameDescr = strip_tags(gameDescr)

				if (gameDescr == ""):
					gameDescr = None

				if (gameDescr):
					grabbed['description'] = transformChars(gameDescr)
			except:
				pass

			try:
				grabbed['publisher'] = transformChars(pagecontent.xpath("//div/text()[contains(.,'Published by')]/../following-sibling::div[1]/a/text()")[0])
			except:
				pass

			try:
				grabbed['developer'] = transformChars(pagecontent.xpath("//div/text()[contains(.,'Developed by')]/../following-sibling::div[1]/a/text()")[0])
			except:
				pass

			try:
				year = transformChars(pagecontent.xpath("//div/text()[contains(.,'Released')]/../following-sibling::div[1]/a/text()")[0])
				grabber['year'] = re.search('\d{4}', str(year)).group(0)
			except:
				pass

			try:
				grabbed['genre'] = transformChars(pagecontent.xpath("//div/text()[contains(.,'Genre')]/../following-sibling::div[1]/a/text()")[0])
			except:
				pass

			if ('url_boxart' not in gameParams):

				try:
					thumbboxartcontent = HTML.ElementFromURL( gameurl + '/cover-art', encoding='utf-8', headers=HTTP_HEADERS )
					thumbboxarturl = thumbboxartcontent.xpath("//div[@class='mobythumbnail']/div//text()[contains(.,'Front Cover')]/../../../div/a/@href")[0]

					boxartcontent = HTML.ElementFromURL( BASE_URL + thumbboxarturl, encoding='utf-8', headers=HTTP_HEADERS )
					grabbed['url_boxart'] = boxartcontent.xpath("//center/img/@src")[0]
				except:
					pass

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
	platform = SYSTEMS_LIST[console.lower()][5]
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

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

