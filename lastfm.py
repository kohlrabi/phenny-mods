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

def generate_api_sig(phenny,params):
  """
  params should be a dictionary of parameters INCLUDING the function name
  """
  concat = [x[0]+x[1] for x in sorted(params.iteritems())]
  out = "".join(concat)
  out += phenny.config.lastfm_secret
     
  out = md5(out).hexdigest()
  
  return out

def auth_user(phenny, origin):
  """
  Uses auth data from the config file
  Config file stores username and md5 hash of password
  (if true, else plaintext in config)
  uses the mobile auth method
  """
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
    lfmkeyfile = open(keypath,'wb')
    pickle.dump(session_key,lfmkeyfile)
    lfmkeyfile.close()
    return session_key
    

def now_playing(phenny, origin):
  
   lastfm_api_key = phenny.config.lastfm_api_key
   uri = 'http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user=%s&limit=1&api_key=%s'
   lfmnames_file = open(os.path.join(configdir,'lfmnames'),'rb')
   lfmnames = pickle.load(lfmnames_file)
   lfmnames_file.close()
   
   phenny.say(key)
  
   nick = origin.nick
   if nick in lfmnames:
     nick = lfmnames[nick]
   if origin.group(2):
     nick = origin.group(2)
     
   nick = urllib.quote(nick.encode('utf-8'))
   
   res = web.get(uri % (nick,lastfm_api_key))
   
   soup = BeautifulStoneSoup(res)
   
   if soup('lfm',status='failed'):
     phenny.say(u"Error: "+soup.error.string)
     return
   else:
     phenny.say(get_nowplaying(soup,nick))
     return
     

def get_nowplaying(soup,nick):
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
    answer = answer.replace(u'&amp;',u'&')

    return answer

def similar(phenny,origin):
    lastfm_api_key = phenny.config.lastfm_api_key
    if origin.group(2):
      artist = origin.group(2).encode('utf-8')
    else:
      phenny.say(u"No artist given.")
      return
   
    uri = 'http://ws.audioscrobbler.com/2.0/?method=artist.getSimilar&limit=5&artist=%s&autocorrect=1&api_key=%s'
   
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
   
    uri = 'http://ws.audioscrobbler.com/2.0/?method=artist.getTags&artist=%s&autocorrect=1&api_key=%s'
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
