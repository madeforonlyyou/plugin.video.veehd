import urllib
import re
import time
import sys
import xbmcplugin
import xbmcgui
import os
import xbmcaddon
import xbmc
import requests
from BeautifulSoup import BeautifulSoup

vhd = xbmcaddon.Addon(id='plugin.video.veehd')
pluginhandle = int(sys.argv[1])

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:12.0'
                         ') Gecko/20100101 Firefox/12.0',
           'Referer': 'http://veehd.com/login'}
LOGIN_URL = 'http://veehd.com/login'


class Borg(object):
    __shared_state = None

    def __init__(self):
        if not Borg.__shared_state:
            Borg.__shared_state = self.__dict__
        else:
            self.__dict__ = Borg.__shared_state


class Veehd(Borg):
    def __init__(self):
        super(Veehd, self).__init__()

        if not hasattr(self, 'req'):
            xbmc.log("Initiating VeeHD object")
            self.req = requests.Session()
            self.cookie, self.index_page = self.login()

    def login(self):
        login_data = {'ref': 'http://veehd.com/dashboard', 'uname': uname,
                      'pword': pwd, 'submit': 'Login', 'terms': 'on',
                      'remember_me': 'on'}
        response = self.req.post(LOGIN_URL, data=login_data, headers=headers)
        if response.url != 'http://veehd.com/dashboard':
            xbmc.log("Login failed. check your username and password")
            dia = xbmcgui.Dialog()
            dia.ok("Login Failed!", "Please check login details")
            vhd.openSettings(sys.argv[0])

        self.download_page("http://veehd.com/cookie?do=nsfw_show")
        return response.cookies, response.text

    def download_page(self, url):
        response = self.req.get(url, headers=headers)
        return response.text, response.status_code

    def list_friends(self, friends_page):
        thumbs = []
        urls = []
        titles = []
        bs = BeautifulSoup(friends_page)
        friends = bs.findAll("div", {"class": ["friend online", "friend "]})
        for div in friends:
            vid_count = int(div('span', {'id': 'userPosted'})[0].text)
            if vid_count == 0:
                # We don't want to display friends with no videos
                continue
            vid_count = "(%s)" % vid_count
            thumbs.append(div('img')[0]['src'])
            p_id = os.path.basename(div('a')[0]['href'])
            urls.append(("%s?url=%s&mode=%s") % (sys.argv[0], p_id, str(5)))
            title = div('img')[0].get('title', None)
            if title:
                titles.append(title + vid_count)
            else:
                titles.append(div('a')[0].get('title') + vid_count)

        frnds = [(thumbs[i], titles[i], urls[i]) for i in range(0, len(urls))]
        for thumb, name, uri in frnds:
            liz = xbmcgui.ListItem(name,
                                   iconImage=thumb)
            liz.setInfo("video", {"Title": name})
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                        url=uri,
                                        listitem=liz,
                                        isFolder=True)
        page = bs.findAll('li', {'class': 'currentpage'})
        next_page = int(page[0].text) + 1
        addDir('Next page', 'http://veehd.com/friends?page=%s' % next_page, 2,
               '')

    def get_video_link(self, url):
        title = ''
        response, code = self.download_page(url)
        if code == 200:
            title = re.findall(r'<title>(.+?) on Veehd</title>', response)
        else:
            return None
        if not title:
            return None
        else:
            title = title[0]
        private_video_url = "http://veehd.com/" + re.findall(r'.*(vpi\?h.*)"',
                                                             response)[1]
        response, code = self.download_page(private_video_url)
        bs = BeautifulSoup(response)
        if not bs('a'):
            # We got a pre-roll ad page
            print "We have got a dud pre-roll video"
            frame_url = bs('iframe')[0]['src']
            response, code = self.download_page('http://veehd.com' + frame_url)
            response, code = self.download_page(private_video_url)
            bs = BeautifulSoup(response)

        vid_url = bs('a')[0]['href']
        return title, vid_url


def CATS():
        addDir('Dashboard', 'http://veehd.com/dashboard?f=all', 2, '')
        addDir('Friends', 'http://veehd.com/friends', 2, '')
        addDir('Channels', 'http', 1, '')
        addDir('Recent', 'http://veehd.com/recent', 2, '')
        addDir('Popular', 'http://veehd.com/popular', 2, '')
        addDir('Search', 'http://veehd.com/', 4, '')


def CHN(url):
        addDir('Animation', 'http://veehd.com/search?tag=animation', 2, '')
        addDir('Art', 'http://veehd.com/search?tag=art', 2, '')
        addDir('Comedy', 'http://veehd.com/search?tag=comedy', 2, '')
        addDir('Educational', 'http://veehd.com/search?tag=educational', 2, '')
        addDir('Games', 'http://veehd.com/search?tag=games', 2, '')
        addDir('Music', 'http://veehd.com/search?tag=music', 2, '')
        addDir('NSFW', 'http://veehd.com/search?tag=nsfw', 2, '')
        addDir('Sport', 'http://veehd.com/search?tag=sport', 2, '')
        addDir('Other', 'http://veehd.com/search?tag=other', 2, '')


def INDEX(url, name):
    vee = Veehd()
    urls = []
    names = []
    thumbs = []
    nxt = []
    if url.startswith("http://veehd.com/dashboard"):
        bs = BeautifulSoup(vee.index_page)
        span_list = bs.findAll('span', {'class': 'tlComment'})
        for span in span_list:
            urls.append(span('a')[0]['href'].split('/')[2])
            names.append(span('a')[0].text)
            thumbs.append(span('img')[0]['src'])
    elif url.startswith("http://veehd.com/friends"):
        xbmc.log("Loading friends page %s" % url)
        text, code = vee.download_page(url)
        xbmc.log("Code=%s" % code)
        if code == 200:
            vee.list_friends(text)
    else:
        xbmc.log("Downloading url: %s" % url)
        page, code = vee.download_page(url)
        thumbs = re.compile('<img id="img.+?" src="(.+?)"').findall(page)
        names = re.compile('<a href="/video/.+?">(.+?)</a>').findall(page)
        urls = re.compile('<a href="/video/(.+?)">.+?</a>').findall(page)
        nxt = re.compile('</a></li><li class="nextpage">'
                         '<a rel="nofollow" href="(.+?)">&raquo;'
                         '</a></li></ul>').findall(page)
    videos = [(thumbs[i], names[i], urls[i]) for i in range(0, len(urls))]
    for thumb, name, url in videos:
        vid_url = 'http://veehd.com/video/' + url
        u = ("%s?url=%s&mode=%s") % (sys.argv[0],
                                     urllib.quote_plus(vid_url, name),
                                     str(3))
        item = xbmcgui.ListItem(name, iconImage=thumb)
        item.setInfo(type="Video", infoLabels={"Title": name})
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=u,
                                    listitem=item)
    for url in nxt:
        addDir('Next page', 'http://veehd.com' + url, 2, '')


def VIDEO(url):
    vee = Veehd()
    try:
        title, video_url = vee.get_video_link(url)
    except Exception as e:
        xbmc.log("Exception parsing video page: %s" % e)
        return None

    if title:
        name = re.sub(r'\s+', '_', title)
    if video_url:
        d_path = os.path.join(vhd.getSetting('download_path'))
        if (vhd.getSetting('download') == '0'):
            dia = xbmcgui.Dialog()
            ret = dia.select('Streaming Options', ['Play', 'Download'])
            if (ret == 0):
                item = xbmcgui.ListItem(path=video_url)
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.setResolvedUrl(pluginhandle, True, item)
            elif (ret == 1):
                path = xbmc.translatePath(d_path, name)
                Download(video_url, path + name + '.avi')
            else:
                return
        elif (vhd.getSetting('download') == '1'):
            item = xbmcgui.ListItem(path=video_url)
            item.setProperty('IsPlayable', 'true')
            xbmcplugin.setResolvedUrl(pluginhandle, True, item)
        elif (vhd.getSetting('download') == '2'):
            path = xbmc.translatePath(d_path, name)
            Download(video_url, path + name + '.avi')
        else:
            item = xbmcgui.ListItem(path=video_url)
            item.setProperty('IsPlayable', 'true')
            xbmcplugin.setResolvedUrl(pluginhandle, True, item)


def SEARCH():
        keyb = xbmc.Keyboard('', 'Search VEEHD')
        keyb.doModal()
        if (keyb.isConfirmed()):
            search = keyb.getText()
            res = requests.get('http://veehd.com/search', params={'q': search})
            link = res.text
        thumbs = re.compile('<img id="img.+?" src="(.+?)"').findall(link)
        names = re.compile('<a href="/video/.+?">(.+?)</a>').findall(link)
        urls = re.compile('<a href="/video/(.+?)">.+?</a>').findall(link)
        videos = [(thumbs[i], names[i], urls[i]) for i in range(0, len(urls))]
        nxt = re.compile('href="(.+?)&page=2">&raquo;</a></li>').findall(link)
        for thumb, name, url in videos:
            vid_url = 'http://veehd.com/video/' + url
            u = ("%s?url=%s&mode=%s") % (sys.argv[0],
                                         urllib.quote_plus(vid_url, name),
                                         str(3))
            item = xbmcgui.ListItem(name, iconImage=thumb)
            item.setInfo(type="Video", infoLabels={"Title": name})
            item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                        url=u,
                                        listitem=item)
        for url in nxt:
            addDir('Next page', 'http://veehd.com' + url + '&page=2', 2, '')


def SHOW_FRIENDS_STUFF(p_id):
    # r_private = 'http://veehd.com/search?private=%s' % p_id
    # pop_private = 'http://veehd.com/search?private=%s&t=pop' % p_id
    r_public = 'http://veehd.com/search?usr=%s' % p_id
    pop_public = 'http://veehd.com/search?usr=%s&t=pop' % p_id
    # addDir('Private - Recent', r_private, 2, '')
    # addDir('Private - Pop', pop_private, 2, '')
    addDir('Public - Popular', pop_public, 2, '')
    addDir('Public - Recent', r_public, 2, '')


def Download(url, dest):
        dp = xbmcgui.DialogProgress()
        dp.create('Downloading', '', name)
        s_time = time.time()
        try:
            urllib.urlretrieve(url, dest, lambda nb, bs, fs: _pbhook(nb,
                                                                     bs,
                                                                     fs,
                                                                     dp,
                                                                     s_time))
        except:
            # delete partially downloaded file
            while os.path.exists(dest):
                try:
                    print 'hello'
                    break
                except:
                    pass
            # only handle StopDownloading (from cancel), ContentTooShort
            # (from urlretrieve), and OS (from the race condition);
            # let other exceptions bubble
            if sys.exc_info()[0] in (urllib.ContentTooShortError,
                                     StopDownloading,
                                     OSError):
                return 'false'
            else:
                raise
        return 'downloaded'


def _pbhook(numblocks, blocksize, filesize, dp, start_time):
        try:
            percent = min(numblocks * blocksize * 100 / filesize, 100)
            currently_downloaded = float(numblocks) * blocksize / (1024 * 1024)
            kbps_speed = numblocks * blocksize / (time.time() - start_time)
            if kbps_speed > 0:
                eta = (filesize - numblocks * blocksize) / kbps_speed
            else:
                eta = 0
            kbps_speed = kbps_speed / 1024
            total = float(filesize) / (1024 * 1024)
            mbs = '%.02f MB of %.02f MB' % (currently_downloaded, total)
            e = 'Speed: %.02f Kb/s ' % kbps_speed
            e += 'ETA: %02d:%02d' % divmod(eta, 60)
            dp.update(percent, mbs, e)
        except:
            percent = 100
            dp.update(percent)
        if dp.iscanceled():
            dp.close()
            raise StopDownloading('Stopped Downloading')


class StopDownloading(Exception):
        def __init__(self, value):
            self.value = value

        def __str__(self):
            return repr(self.value)


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params)-1] == '/'):
            params = params[0:len(params)-2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param


def addDir(name, url, mode, thumbnail):
        u = ("%s?url=%s&mode=%s&name=%s") % (sys.argv[0],
                                             urllib.quote_plus(url),
                                             str(mode),
                                             urllib.quote_plus(name))
        ok = True
        liz = xbmcgui.ListItem(name,
                               iconImage="defaultfolder.png",
                               thumbnailImage=thumbnail)
        liz.setInfo("video", {"Title": name})
        ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                         url=u,
                                         listitem=liz,
                                         isFolder=True)
        return ok


def addLink(name, url, iconimage, plot, date):
        ok = True
        liz = xbmcgui.ListItem(name,
                               iconImage="DefaultVideo.png",
                               thumbnailImage=iconimage)
        liz.setInfo(type="Video", infoLabels={"Title": name})
        liz.setInfo(type="Video", infoLabels={"Plot": plot})
        liz.setInfo(type="Video", infoLabels={"Date": date})
        liz.setProperty("IsPlayable", "true")
        ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url,
                                         listitem=liz,
                                         isFolder=False)
        return ok


def check_settings():
        uname = vhd.getSetting('uname')
        pwd = vhd.getSetting('pwd')
        if (not uname or uname == '') or (not pwd or pwd == ''):
                d = xbmcgui.Dialog()
                d.ok('Welcome to veehd.com', "To start using this plugin first"
                                             "go to veehd.com",
                                             "and create an (free) account.")
                vhd.openSettings(sys.argv[0])


params = get_params()
url = None
name = None
mode = None

check_settings()
uname = vhd.getSetting('uname')
pwd = vhd.getSetting('pwd')

try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass

if mode is None or url is None or len(url) < 1:
    xbmc.log("Show Categories")
    CATS()
elif mode == 1:
    xbmc.log("Channels - PAGE")
    CHN(url)
elif mode == 2:
    xbmc.log("Calling Index with url=%s, name=%s" % (url, name))
    INDEX(url, name)
elif mode == 3:
    xbmc.log("Video - url=%s" % url)
    VIDEO(url)
elif mode == 4:
    xbmc.log("Search - url=%s" % url)
    SEARCH()
elif mode == 5:
    xbmc.log("Friends")
    SHOW_FRIENDS_STUFF(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
