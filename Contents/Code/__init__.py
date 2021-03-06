import re, sesame

NAME = 'PornHub'
BASE_URL = 'http://www.pornhub.com'
CATEGORIES = '%s/categories' % BASE_URL

VIDEO_SORT_ORDER = [
	['Most Recent', 'o=mr'],
	['Top Rated - Daily', 'o=tr&t=t'],
	['Top Rated - Weekly', 'o=tr&t=w'],
	['Top Rated - Monthly', 'o=tr&t=m'],
	['Top Rated - All time', 'o=tr&t=a'],
	['Most Viewed - Daily', 'o=mv&t=t'],
	['Most Viewed - Weekly', 'o=mv&t=w'],
	['Most Viewed - Monthly', 'o=mv&t=m'],
	['Most Viewed - All time', 'o=mv&t=a'],
	['Longest', 'o=lg']
]

ART = 'art-default.jpg'
ICON = 'icon-default.png'
ICON_MORE = 'icon-more.png'

####################################################################################################
def Start():

	Plugin.AddPrefixHandler('/video/pornhub', MainMenu, NAME, ICON, ART)
	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
	Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

	MediaContainer.art = R(ART)
	MediaContainer.title1 = NAME
	MediaContainer.viewGroup = 'InfoList'
	DirectoryItem.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0'

####################################################################################################
def MainMenu():

	dir = MediaContainer()
	dir.Append(Function(DirectoryItem(SortOrder, title='All'), category='/video'))

	for category in HTML.ElementFromURL(CATEGORIES, cacheTime=CACHE_1WEEK).xpath('//li[@class="cat_pic"]'):
		title = category.xpath('.//strong')[0].text.strip()
		thumb = category.xpath('.//a/img')[0].get('src')
		url = category.xpath('.//a')[0].get('href')
		dir.Append(Function(DirectoryItem(SortOrder, title=title, thumb=Function(GetThumb, url=thumb)), category=url))

	dir.Sort('title')
	return dir

####################################################################################################
def SortOrder(sender, category):

	dir = MediaContainer(title2=sender.itemTitle)

	for (sort_title, sort) in VIDEO_SORT_ORDER:
		dir.Append(Function(DirectoryItem(VideoList, title=sort_title), category=category, sort=sort, title=sender.itemTitle))

	return dir

####################################################################################################
def VideoList(sender, category, sort, title, page=1):

	dir = MediaContainer(title2=title)

	if '?' in category:
		full_url = '%s%s&%s&page=%d' % (BASE_URL, category, sort, page)
	else:
		full_url = '%s%s?%s&page=%d' % (BASE_URL, category, sort, page)

	video = HTML.ElementFromURL(full_url)

	for v in video.xpath('//li[contains(@class,"videoblock")]'):
		video_title = v.xpath('.//a[@class="title"]')[0].text.strip()
		video_page = v.xpath('.//a')[0].get('href')
		duration = TimeToSeconds(v.xpath('.//var[@class="duration"]')[0].text) * 1000
		thumb = v.xpath('.//img')[0].get('data-mediumthumb')
		try:
			rating = float( v.xpath('.//div[contains(@class,"rating")]/div[@class="value"]')[0].text.replace('%','') ) / 10
		except:
			rating = None

		dir.Append(Function(VideoItem(PlayVideo, title=video_title, duration=duration, rating=rating, thumb=Function(GetThumb, url=thumb)), url=video_page))

	if len(video.xpath('//li[@class="page_next"]')) > 0:
		dir.Append(Function(DirectoryItem(VideoList, title='Next page...', thumb=R(ICON_MORE)), category=category, sort=sort, title=title, page=page+1))

	return dir

####################################################################################################
def PlayVideo(sender, url):

	page = HTTP.Request(url, cacheTime=1).content

	video_title = re.search('"video_title":"([^"]+)"', page).group(1)
	video_title = String.Unquote(video_title, usePlus=True)

	video_url = re.search('"quality_\d+p":"([^"]+)"', page).group(1)
	video_url = String.Unquote(video_url, usePlus=True)

	video_url = sesame.decrypt(video_url, video_title, 256)
	#Log('video_url: %s' % video_url)

	return Redirect(VideoItem(video_url))

####################################################################################################
def GetThumb(url):

	try:
		data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
		return DataObject(data, 'image/jpeg')
	except:
		pass

	return Redirect(R(ICON))

####################################################################################################
def TimeToSeconds(timecode):

	seconds  = 0
	duration = timecode.split(':')
	duration.reverse()

	for i in range(0, len(duration)):
		seconds += int(duration[i]) * (60**i)

	return seconds
