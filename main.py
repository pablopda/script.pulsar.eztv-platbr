import sys
import os
import json
import base64
import urllib2
import hashlib
import time
import re
import xbmcplugin
from fuzzywuzzy import fuzz

inicio = time.time()

PREFIX_LOG = 'EZTV - '
BASE_URL = "https://eztv.it"
HEADERS = { 'Referer' : BASE_URL,
            'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36'
}

cache_age = 12 * 60 * 60
use_fuzzy = True
# threshold recommended 90-97
fuzzy_threshold = 92

def search(query):
    return []

def search_movie(imdb_id, name, year):
    return []

def search_episode(imdb_id,tvdb_id,name,season,episode):
    show_list = get_eztv_shows()
    episode_string = '(?:S' + str(season).zfill(2) + 'E' + str(episode).zfill(2) + '|' + str(season) + 'x' + str(episode).zfill(2) + ')'
    print PREFIX_LOG + 'Seaching for: ' + name + ' (' + str(season).zfill(2) + 'E' + str(episode).zfill(2) + ')'
    result = []
    show_found = ''
    for item in show_list:
        if ((name == item['name1']) | (name == item['name2']) | (name == item['name3']) | (name == item['name4'])):
            url_show = BASE_URL + '/shows/' + item['id'] + '/'
            req = urllib2.Request(url_show, headers=HEADERS)
            data = urllib2.urlopen(req).read()
            for magnet in re.findall(r'(magnet.*' + episode_string + '.*)" class="magnet"', data, re.IGNORECASE):
                result.append({'uri': magnet})
            show_found = name
            break
    if(show_found):
        print PREFIX_LOG + 'Show found: ' + show_found
    else:
        print PREFIX_LOG + 'Show found: none'
        if(use_fuzzy):
            print PREFIX_LOG + 'Trying Fuzzy'
            fuzy_list = []
            for item in show_list:
                fuzy_list.append({'score': int(fuzz.ratio(name,item['name1'])), 'id': item['id'], 'name': item['name1']})
                fuzy_list.append({'score': int(fuzz.ratio(name,item['name2'])), 'id': item['id'], 'name': item['name2']})
                fuzy_list.append({'score': int(fuzz.ratio(name,item['name3'])), 'id': item['id'], 'name': item['name3']})
                fuzy_list.append({'score': int(fuzz.ratio(name,item['name4'])), 'id': item['id'], 'name': item['name4']})
            def getKey(obj):
                return obj['score']
            sorted_showlist = sorted(fuzy_list, key=getKey)
            item = sorted_showlist[-1]
            if(item['score'] >= fuzzy_threshold ):
                print PREFIX_LOG + 'Fuzzy found: ' + item['name'] + ' (score: ' + str(item['score']) + ')'
                url_show = BASE_URL + '/shows/' + item['id'] + '/'
                req = urllib2.Request(url_show, headers=HEADERS)
                data = urllib2.urlopen(req).read()
                for magnet in re.findall(r'(magnet.*' + episode_string + '.*)" class="magnet"', data, re.IGNORECASE):
                    result.append({'uri': magnet})
            else:
                print PREFIX_LOG + 'Fuzzy ignored: ' + sorted_showlist[-1]['name'] + ' (score: ' + str(sorted_showlist[-1]['score'])+ ')'

    print PREFIX_LOG + 'Result: ' + str(result)
    print PREFIX_LOG + 'Time: ' + str((time.time() - inicio))
    return result

def get_eztv_shows():
    data = get_cached_url(BASE_URL + '/showlist/')
    eztv_shows = []
    for show_id, show_named_id, show_name in re.findall(r'<a href="/shows/([0-9][0-9]*)/(.*)/" class="thread_link">(.*)</a></td>', data):
        name1 = re.sub('[-]', ' ', show_named_id)
        t1 = re.sub('[&]', 'and', show_name)
        s1 = re.sub('\([^)A-Z]*\)|[\(\)\':]', '', t1)
        s2 = re.sub('\([^)]*\)|[\(\)\':]', '', t1)
        s3 = re.sub('[\(\)\':]', '', t1)
        f1 = re.findall(r'(.*),(.*)', s1, re.IGNORECASE)
        f2 = re.findall(r'(.*),(.*)', s2, re.IGNORECASE)
        f3 = re.findall(r'(.*),(.*)', s3, re.IGNORECASE)
        if(len(f1) > 0):
            name2 = f1[0][1] + ' ' + f1[0][0]
            name3 = f2[0][1] + ' ' + f2[0][0]
            name4 = f3[0][1] + ' ' + f3[0][0]
        else:
            name2 = s1
            name3 = s2
            name4 = s3
        eztv_shows.append({
            "id": show_id,
            "name1": name1.lower().strip(),
            "name2": name2.lower().strip(),
            "name3": name3.lower().strip(),
            "name4": name4.lower().strip(),
        })
    return eztv_shows

def get_cached_url(url):
    data = ''
    m = hashlib.md5()
    m.update(url)
    url_hash = m.hexdigest()
    cache_file = xbmc.translatePath('special://temp') + url_hash
    print PREFIX_LOG + 'Cache -> ' + cache_file
    if(os.path.isfile(cache_file)):
        if ((time.time() - os.stat(cache_file).st_mtime)  > cache_age):
            print PREFIX_LOG + 'Invalid cache!'
            req = urllib2.Request(url, headers=HEADERS)
            data = urllib2.urlopen(req).read()
            f = open(cache_file, "w")
            f.write(data)
            f.close()
        else:
            f = open(cache_file, "r")
            data = f.read()
            f.close()
    else:
        print PREFIX_LOG + 'No cache!'
        req = urllib2.Request(url, headers=HEADERS)
        data = urllib2.urlopen(req).read()
        f = open(cache_file, "w")
        f.write(data)
        f.close()
    return data

PAYLOAD = json.loads(base64.b64decode(sys.argv[1]))
urllib2.urlopen(
PAYLOAD["callback_url"],
data=json.dumps(globals()[PAYLOAD["method"]](*PAYLOAD["args"]))
)
