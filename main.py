import sys
import os
import json
import base64
import urllib
import urllib2
import time
import re
import xbmcplugin

inicio = time.time()
BASE_URL = "https://eztv.it"
HEADERS = { 'Referer' : BASE_URL,
            'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36'
}
cache_file = xbmc.translatePath('special://temp') + "eztv_showlist.html"
cache_age = 12 * 60 * 60
eztv_shows = []
def get_eztv_shows():
    if(os.path.isfile(cache_file)):
        if ((time.time() - os.stat(cache_file).st_mtime)  > cache_age):
            print 'Invalid cache!'
            req = urllib2.Request('%s/showlist/' % BASE_URL, headers=HEADERS)
            data = urllib2.urlopen(req).read()
            f = open(cache_file, "w")
            f.write(data)
            f.close()
        else:
            f = open(cache_file, "r")
            data = f.read()
            f.close()
    else:
        print 'No cache!'
        req = urllib2.Request('%s/showlist/' % BASE_URL, headers=HEADERS)
        data = urllib2.urlopen(req).read()
        f = open(cache_file, "w")
        f.write(data)
        f.close()
    for show_id, show_named_id, show_name in re.findall(r'<a href="/shows/([0-9][0-9]*)/(.*)/" class="thread_link">(.*)</a></td>', data):
        name_alt = re.sub('[-]', ' ', show_named_id)
        replaced = re.sub('\([^)]*\)|[\':]', '', show_name)
        fix_position = re.findall(r'(.*),(.*)', replaced, re.IGNORECASE)
        if(len(fix_position) > 0):
            new_name = fix_position[0][1] + ' ' + fix_position[0][0]
        else:
            new_name = replaced
        eztv_shows.append({
            "id": show_id,
            "name": new_name.lower(),
            "name_alt": name_alt.lower(),
        })
        #print show_name + ' -> ' + new_name
    return eztv_shows

def search_episode(imdb_id,tvdb_id,name,season,episode):
    result = []
    show_list = get_eztv_shows()
    episode_string = 'S' + str(season).zfill(2) + 'E' + str(episode).zfill(2)
    print 'EZTV - Seaching for: ' + name + ' ' + episode_string
    for item in show_list:
        if ((name == item['name']) | (name == item['name_alt'])):
            url_show = BASE_URL + '/shows/' + item['id'] + '/'
            req = urllib2.Request(url_show, headers=HEADERS)
            data = urllib2.urlopen(req).read()
            for magnet in re.findall(r'(magnet.*' + episode_string + '.*)" class="magnet"', data, re.IGNORECASE):
                result.append({'uri': magnet})
    print 'EZTV - Result: ' + str(result)
    print 'EZTV - Time:' + str((time.time() - inicio))

def search(query):
    return []

def search_movie(imdb_id, name, year):
    return []

PAYLOAD = json.loads(base64.b64decode(sys.argv[1]))
urllib2.urlopen(
PAYLOAD["callback_url"],
data=json.dumps(globals()[PAYLOAD["method"]](*PAYLOAD["args"]))
)
