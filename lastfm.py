#!/usr/bin/env python
"""
lastfm.py - Phenny last.fm Module
Copyright 2011, Christoph Terasa 
Licensed under the WTFPL.
"""
import cPickle as pickle
import re, urllib, os
import web
from tools import deprecated
from BeautifulSoup import BeautifulStoneSoup
from hashlib import md5

configdir = os.path.expanduser('~/.phenny/')
childish_include = True
get_playcount = True

def setup(phenny):
  phenny.lastfm_session_key = auth_user(phenny)

def generate_api_sig(phenny,params):
  """
  params should be a dictionary of parameters INCLUDING the function name
  """
  concat = [x[0]+x[1] for x in sorted(params.iteritems())]
  out = "".join(concat)
  out += phenny.config.lastfm_secret
     
  out = md5(out).hexdigest()
  
  return out

def auth_user(phenny,pickle_key=False):
  """
  Uses auth data from the config file
  Config file stores username and md5 hash of password
  (if true, else plaintext in config)
  uses the mobile auth method
  """
  if pickle_key:
    keypath = os.path.join(configdir,'lfmkey')
    if os.path.exists(keypath):
      lfmkeyfile = open(keypath,'rb')
      session_key = pickle.load(lfmkeyfile)
      lfmkeyfile.close()
      return session_key
    
  pw_hashed = False
  
  username = phenny.config.lastfm_username
  password = phenny.config.lastfm_password
  if not pw_hashed:
    password = md5(password).hexdigest()

  auth_token = md5(username+password).hexdigest()
  
  lastfm_api_key = phenny.config.lastfm_api_key
  #lastfm_secret = phenny.config.lastfm_secret
  
  method = u"auth.getMobileSession"
  sig_dict = {u"api_key":lastfm_api_key,u"authToken":auth_token,u"username":username,"method":method}
  
  api_sig = generate_api_sig(phenny,sig_dict)
  
  uri = u'http://ws.audioscrobbler.com/2.0/?method=auth.getMobileSession&username=%s&authToken=%s&api_key=%s&api_sig=%s'
  
  res = web.get(uri % (username,auth_token,lastfm_api_key,api_sig))
    
  soup = BeautifulStoneSoup(res)
  
  if soup('lfm',status='failed'):
    phenny.say(u"Error: Authentication failed.")
    return
  else:
    session_key = soup.lfm.session.key.string
    if pickle_key:
      lfmkeyfile = open(keypath,'wb')
      pickle.dump(session_key,lfmkeyfile)
      lfmkeyfile.close()
    return session_key
    

def now_playing(phenny, origin):
  lastfm_api_key = phenny.config.lastfm_api_key
  uri = u'http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user=%s&limit=1&api_key=%s'
  lfmnames_file = open(os.path.join(configdir,'lfmnames'),'rb')
  lfmnames = pickle.load(lfmnames_file)
  lfmnames_file.close()
  
  currently_playing = False
  
  nick = origin.nick
  if nick in lfmnames:
    nick = lfmnames[nick]
  if origin.group(2):
    nick = origin.group(2)
   
  nick = urllib.quote(nick.encode('utf-8'))

  res = web.get(uri % (nick,lastfm_api_key))

  soup = BeautifulStoneSoup(res)
  if soup('lfm',status='failed'):
    phenny.say(u"Error: "+soup.lfm.error.string)
    return
  elif not soup.lfm.recenttracks.track:
    phenny.say(u"No recent tracks found for %s."%nick)
    return
  
  np_track = soup.lfm.recenttracks('track',nowplaying="true")
  if(np_track):
    currently_playing = True
  else:
    currently_playing = False
    #answer = u'%s is currently not listening to or scrobbling any music :-('%nick
    #phenny.say(answer)
    #return
  np_track=soup.lfm.recenttracks.track

  if get_playcount:
    mbid = np_track.mbid.string
    if mbid:
      uri2 = 'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&mbid=%s&username=%s&api_key=%s'
      res2 = web.get(uri2 % (mbid,nick,lastfm_api_key))
    else:
      artist = np_track.artist.string
      artist = urllib.quote(artist.encode('utf-8'))
      track = np_track('name')[0].string
      track = urllib.quote(track.encode('utf-8'))
      uri2 = 'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&artist=%s&track=%s&username=%s&api_key=%s'
      res2 = web.get(uri2 % (artist,track,nick,lastfm_api_key))
        
    soup2 = BeautifulStoneSoup(res2)
    if get_playcount and soup2('lfm',status='failed'):
      phenny.say(u"Error: "+soup2.lfm.error.string)
      return
  
    	
 
    if get_playcount:
      phenny.say(get_nowplaying(currently_playing,soup,nick,soup2))
    else:
      phenny.say(get_nowplaying(currently_playing,soup,nick))
    return
     

def get_nowplaying(currently_playing,soup,nick,soup2=None):
  np_track = soup.lfm.recenttracks.track
  artist = np_track.artist.string
  name_tag = np_track('name')[0]
  name = name_tag.string
  album = np_track.album.string

  if get_playcount:
    np_track2 = soup2.lfm.track
    global_playcount = np_track2.playcount.string
    num_listeners = np_track2.listeners.string
    userplaycount = np_track2.userplaycount.string
    userloved = int(np_track2.userloved.string)
 
  if userloved == 1:
    note = u'\u2665'
  else:
    note = u'\u266B'
 
  if currently_playing:
    prefix = u'%s is currently listening to %s '%(nick,note)
  else:
    date = np_track.date.string
    prefix = u'On %s %s has listened to %s '%(date,nick,note)
  postfix =  u' %s'%note
  if album:
    song =  u'%s - [%s] - %s'%(artist,album,name)
  else:
    song = u'%s - %s'%(artist,name)
    

  if get_playcount:
    pc = u' | %s plays by %s, %s plays by %s listeners.'%(userplaycount,nick,global_playcount,num_listeners)
  else:
    pc = u''
  
  
  answer = prefix + song + postfix + pc
  answer = answer.replace(u'&amp;',u'&')

  return answer

def similar(phenny,origin):
    lastfm_api_key = phenny.config.lastfm_api_key
    if origin.group(2):
      artist = origin.group(2).encode('utf-8')
    else:
      phenny.say(u"No artist given.")
      return
   
    uri = u'http://ws.audioscrobbler.com/2.0/?method=artist.getSimilar&limit=5&artist=%s&autocorrect=1&api_key=%s'
   
    res = web.get(uri % (artist,lastfm_api_key))
   
    soup = BeautifulStoneSoup(res)
   
    if soup('lfm',status='failed'):
      phenny.say(u"Error: "+soup.error.string)
      return
    else:
      multiline = False
      sim = get_similar(soup,multiline)
      if multiline:      
	for s in sim:
	  phenny.say(s)
      else:
	  phenny.say(sim)
      return
     
def get_similar(soup,multiline=False):
    node = soup.lfm.similarartists
    
    artist = node['artist']
    
    if multiline:
      out = u"\n"
    else:
      out = u""    
    
    allart = node.findAll(name='artist')
    for i in allart:
      if multiline:
	out += i('name')[0].string+u"\n"
      else:
	out += i('name')[0].string+u" | "

    output = u"Similar artists to %s: %s"%(artist,out)
    
    output = output.replace(u'&amp;',u'&')
    
    if multiline:
      return output.split(u"\n")
    else:
      return output[:-3]
      
def tags(phenny,origin):
    lastfm_api_key = phenny.config.lastfm_api_key
    if origin.group(2):
      artist = origin.group(2).encode('utf-8')
    else:
      phenny.say(u"No artist given.")
      return
      
    soup_dict = {}
   
    uri = u'http://ws.audioscrobbler.com/2.0/?method=artist.getTags&artist=%s&autocorrect=1&api_key=%s'
    res = web.get(uri % (artist,lastfm_api_key))
   
    soup = BeautifulStoneSoup(res)
      
    if soup('lfm',status='failed'):
      phenny.say(u"Error: "+soup.error.string)
      return
    else:
      multiline = False
      sim = get_similar(soup,multiline)
      if multiline:      
	for s in sim:
	  phenny.say(s)
      else:
	  phenny.say(sim)
      return
     
def get_tags(soup):
    node = soup.lfm.similarartists
    
    artist = node['artist']
    
    if multiline:
      out = u"\n"
    else:
      out = u""    
    
    allart = node.findAll(name='artist')
    for i in allart:
      if multiline:
	out += i('name')[0].string+u"\n"
      else:
	out += i('name')[0].string+u" | "

    output = u"Similar artists to %s: %s"%(artist,out)
    
    output = output.replace(u'&amp;',u'&')
    
    if multiline:
      return output.split(u"\n")
    else:
      return output[:-3]

   
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
  
similar.commands = ['lfmsim','sim']   
now_playing.commands = ['lfm','np']
regname.commands = ['reglfm','lfmreg']
auth_user.commands = ['lfmauth']

if __name__ == '__main__': 
   print __doc__.strip()
