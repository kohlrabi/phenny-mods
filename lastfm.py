#!/usr/bin/env python
"""
lastfm.py - Phenny Dictionary Module
Copyright 2011, Christoph Terasa 
Licensed under the .

http://inamidst.com/phenny/
"""
import cPickle as pickle
import re, urllib, os
import web
from tools import deprecated
from BeautifulSoup import BeautifulStoneSoup

configdir = os.path.expanduser('~/.phenny/')
childish_include = True

def get_answer(soup,nick):
    np_track = soup.lfm.recenttracks('track',nowplaying="true")
    if(np_track):
      np_track=np_track[0]
    else:
      answer = u'%s is currently not listening to or scrobbling any music :-('%nick
      return answer
    artist = np_track.artist.string
    name_tag = np_track('name')[0]
    name = name_tag.string
    album = np_track.album.string
		
    prefix = u'%s is currently listening to \u266B '%nick
    postfix =  u' \u266B'
    if album:
      song =  u'%s - [%s] - %s'%(artist,album,name)
    else:
      song = u'%s - %s'%(artist,name)
    
    answer = prefix + song + postfix
    return answer


def lastfm(phenny, origin):
  
   lastfm_api_key = phenny.config.lastfm_api_key
   uri = 'http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user=%s&limit=1&api_key=%s'
   lfmnames_file = open(os.path.join(configdir,'lfmnames'),'rb')
   lfmnames = pickle.load(lfmnames_file)
   lfmnames_file.close()
  
   nick = origin.nick
   if nick in lfmnames:
     nick = lfmnames[nick]
   if origin.group(2):
     nick = origin.group(2)
     
   nick = urllib.quote(nick.encode('utf-8'))
   
   res = web.get(uri % (nick,lastfm_api_key))
   
   soup = BeautifulStoneSoup(res)
   
   if soup('lfm',status='failed'):
     phenny.say('Error: '+soup.error.string)
     return
   else:
     phenny.say(get_answer(soup,nick))
     return
   
def regname(phenny, origin):
  
   lfmnames_file = open(os.path.join(configdir,'lfmnames'),'rb')
   lfmnames = pickle.load(lfmnames_file)
   lfmnames_file.close()
  
   split_or = origin.group(2).split()
   if len(split_or) >= 2:
     if childish_include:
      phenny.say("Error: Too many parameters.")
      return
     else:
      nick=split_or[0]
      lfmnick=''.join(split_or[1:])
   else:
     nick=origin.nick
     lfmnick = split_or[0]
   
  
   lfmnames.update({nick:lfmnick})
  
   lfmnames_file = open(os.path.join(configdir,'lfmnames'),'wb')
   pickle.dump(lfmnames,lfmnames_file)
   lfmnames_file.close()
  
   phenny.say('IRC nickname %s registered to last.fm nickname %s.'%(nick,lfmnick))
   return
  
   
lastfm.commands = ['lfm','np']
regname.commands = ['reglfm','lfmreg']

if __name__ == '__main__': 
   print __doc__.strip()
