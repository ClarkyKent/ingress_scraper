#! /usr/local/bin/python
#-*- coding: utf-8 -*-
import requests
import re, sys
import lxml
import json
from datetime import datetime
from time import time
import getpass
from bs4 import BeautifulSoup as bs
from requests.utils import dict_from_cookiejar, cookiejar_from_dict
import math
__AUTHOR__ = 'lc4t0.0@gmail.com'


def get_tiles_per_edge(zoom):
    if zoom > 15:
        zoom = 15
    elif zoom < 3:
        zoom = 3
    else:
        pass
    return [1, 1, 1, 40, 40, 80, 80, 320, 1000, 2000, 2000, 4000, 8000, 16000, 16000, 32000][zoom]


def lng2tile(lng, tpe): # w
  return int((lng + 180) / 360 * tpe);

def lat2tile(lat, tpe): # j
    return int((1 - math.log(math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)) / math.pi) / 2 * tpe)

def tile2lng(x, tpe):
    return x / tpe * 360 - 180;

def tile2lat(y, tpe):
    n = math.pi - 2 * math.pi * y / tpe;
    return 180 / math.pi * math.atan(0.5 * (math.exp(n) - math.exp(-n)));
    
    

class MapTiles:

    def __init__(self, bbox):
        self.LowerLng = bbox[0]
        self.LowerLat = bbox[1]
        self.UpperLng = bbox[2]
        self.UpperLat = bbox[3]
        self.zpe = get_tiles_per_edge(15)
        self.tiles = []
        
    def getTiles(self):        
        Lx = lng2tile(self.LowerLng, self.zpe)
        Ly = lat2tile(self.LowerLat, self.zpe)
        Ux = lng2tile(self.UpperLng, self.zpe)
        Uy = lat2tile(self.UpperLat, self.zpe)

        for x in range(Lx, Ux+1):
            for y in range(Uy, Ly+1):
                self.tiles.append([x,y])

        return self.tiles

class IntelMap:
    r = requests.Session()
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.8',
        'content-type': 'application/json; charset=UTF-8',
        'origin': 'https://intel.ingress.com',
        'referer': 'https://intel.ingress.com/intel',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
    }
    data_base = {
        'v': '',
    }
    proxy = {
        # 'http': 'socks5://127.0.0.1:1080',
        # 'https': 'socks5://127.0.0.1:1080',
    }
    def __init__(self, cookie):
        self.login(cookie)
        self.isCookieOk = False

    def login(self, cookie):
        try:
            self.cookie_dict = {k.strip():v for k,v in re.findall(r'(.*?)=(.*?);', cookie)}
            s = requests.Session()
            s.cookies = cookiejar_from_dict(self.cookie_dict)
            test = s.get('https://intel.ingress.com/intel', proxies=self.proxy)
            self.data_base['v'] = re.findall('/jsc/gen_dashboard_([\d\w]+).js"', test.text)[0]
            self.r = s
            print('cookies success')
            self.cookie_dict = dict_from_cookiejar(self.r.cookies)
            self.headers.update({'x-csrftoken': self.cookie_dict['csrftoken']})
            self.isCookieOk = True
        except IndexError:
            print("Oops!, looks like you have a problem with your cookie.")
            self.isCookieOk = False


    def get_game_score(self):
        data = self.data_base
        data = json.dumps(data)
        _ = self.r.post('https://intel.ingress.com/r/getGameScore', data=data, headers=self.headers, proxies=self.proxy)
        print(_.text)
        return json.loads(_.text)

    def get_entities(self, tilenames):
        _ = {
          "tileKeys": tilenames,    # ['15_25238_13124_8_8_100']
        }
        data = self.data_base
        data.update(_)
        data = json.dumps(data)
        _ = self.r.post('https://intel.ingress.com/r/getEntities', data=data, headers=self.headers, proxies=self.proxy)
        return json.loads(_.text)

    def get_portal_details(self, guid):
        _ = {
          "guid": guid, # 3e2bcc15c58d486fae24e2ade2bf7327.16
        }
        data = self.data_base
        data.update(_)
        data = json.dumps(data)
        _ = self.r.post('https://intel.ingress.com/r/getPortalDetails', data=data, headers=self.headers, proxies=self.proxy)
        try:
            return json.loads(_.text)
        except Exception as e:
            return None
         

    def get_plexts(self, min_lng, max_lng, min_lat, max_lat, tab='all', maxTimestampMs=-1, minTimestampMs=0, ascendingTimestampOrder=True):
        if minTimestampMs == 0:
            minTimestampMs = int(time()*1000)
        data = self.data_base
        data.update({
            'ascendingTimestampOrder': ascendingTimestampOrder,
            'maxLatE6': max_lat,
            'minLatE6': min_lat,
            'maxLngE6': max_lng,
            'minLngE6': min_lng,
            'maxTimestampMs': maxTimestampMs,
            'minTimestampMs': minTimestampMs,
            'tab': tab,
        })
        data = json.dumps(data)
        _ = self.r.post('https://intel.ingress.com/r/getPlexts', headers=self.headers, data=data, proxies=self.proxy)
        return json.loads(_.text)

    def send_plexts(self, lat, lng, message, tab='faction'):
        data = self.data_base
        data.update({
            'latE6': lat,
            'lngE6': lng,
            'message': message,
            'tab': tab,
        })
        data = json.dumps(data)
        _ = self.r.post('https://intel.ingress.com/r/sendPlext', headers=self.headers, data=data, proxies=self.proxy)
        return json.loads(_.text)

    def get_region_score_details(self, lat, lng):
        data = self.data_base
        data.update({
            'latE6': lat,   # 30420109, 104938641
            'lngE6': lng,
        })
        data = json.dumps(data)
        _ = self.r.post('https://intel.ingress.com/r/getRegionScoreDetails', headers=self.headers, data=data, proxies=self.proxy)
        return json.loads(_.text)

