#!/usr/bin/env python
"""
dict.py - Phenny Dictionary Module
Copyright 2008-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://inamidst.com/phenny/
"""

import re, urllib
import web
from tools import deprecated
from BeautifulSoup import BeautifulStoneSoup

r_li = re.compile(r'(?ims)<li>.*?</li>')
r_tag = re.compile(r'<[^>]+>')
r_parens = re.compile(r'(?<=\()(?:[^()]+|\([^)]+\))*(?=\))')
r_word = re.compile(r'^[A-Za-z0-9\' -]+$')

uri = 'http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user=%s&limit=1&api_key=d79a33d26929cc5ebe75411c0864f6be'
r_info = re.compile(
   r'(?:ResultBody"><br /><br />(.*?)&nbsp;)|(?:<b>(.*?)</b>)'
)

def lastfm(phenny, origin):
   nick = origin.nick
   nick = urllib.quote(nick.encode('utf-8'))
   
   res = web.get(uri % nick)
   
   soup = BeautifulStoneSoup(res)
   
   def get_answer():
    np_track = soup.lfm.recenttracks('track',nowplaying="true")
    if(np_track):
      np_track=np_track[0]
    else:
      answer = '%s is currently not listening to or scrobbling any music :-('%nick
      return answer
    artist = np_track.artist.string
    name_tag = np_track('name')[0]
    name = name_tag.string
    album = np_track.album.string
		
    prefix = '%s is currently listening to * '%nick
    postfix =  ' *'
    if album:
      song =  '%s - [%s] - %s'%(artist,album,name)
    else:
      song = '%s - %s'%(artist,name)
    
    answer = prefix + song + postfix
    return answer
   
   phenny.say(get_answer())
   return
   
lastfm.commands = ['lfm']

if __name__ == '__main__': 
   print __doc__.strip()
