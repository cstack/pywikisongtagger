#!/usr/bin/python

#
# Pywiki Song Tagger
#
# Connor Stack
#
# Version 0.1
#
# 8/25/08
#

"""
Looks up a song on Wikipedia and tags the file with retrieved information.

To tag a single file, use:
    tag_file("C:\the\file\location.mp3")

To tag all the files in a folder, use:
    tag_folder("C:\the\folder\directory")

Information about each tagging attempt in recorded in log.txt

Default file and folder are declared below. Change them to whatever you want.
    
"""

# Declare default locations
default_folder = 'Test Music'
default_file = 'Test Music\David Byrne - The Wired CD Rip. Sample. Mash. Share - 02 - My Fair Lady.mp3'

# Import
import sys
sys.path.append("J:\\wikisongtagger\\pywikipedia")
sys.path.append("J:\\wikisongtagger\\mutagen")
import mutagen,os,re,time,wikipedia
from mutagen.easyid3 import EasyID3

def tag_folder(folder = default_folder):
    # Get list of files
    file_list = []
    for item in os.listdir(folder):
        file_list.append(folder + "\\" + item)

    # Tag each file
    for file in file_list:
        print tag_file(file)

def tag_file(file = default_file):

    # open log
    global log
    log = open("log.txt", "a")
    log.write(time.strftime("\n\n%Y - %m - %d %H:%M:%S"))

    # Read tags off mp3 file
    audio = EasyID3(file)
    try:
        title = audio["title"][0]
        print "Title:", title
        log.write("\nTitle: " + title)
    except:
        log.write("\nCan not look up song because title is missing")
        log.close()
        return "Can not look up song because title is missing"
    try:
        album = audio["album"][0]
        log.write("\nAlbum: " + album)
        print "Album:", album
    except:
        log.write("\nAlbum is missing")
        print "Album is missing"
        
    # Find Page on Wikipedia
    text = locate_page(title, "song")

    if text != "NoPage":
        tags = parse_song(text)
    else:
        log.write("\nLooking up song on album page")
        print "\nLooking up song on album page"
        try:
            text = locate_page(album, "album")
            if text == "NoPage":
                log.write("\nThe song could not be found")
                log.close()
                return "The song could not be found"
            tags = parse_album(text, title)
        except:
            log.write("\nThe song could not be found")
            log.close()
            return "The song could not be found"

    # Print the found tags
    for tag in tags:
        log.write("\n" + tag + " : " + tags[tag])
        print tag, ":", tags[tag]

    # Tag the file
    for tag in tags:
        audio[tag] = tags[tag]
        
    try:
        audio.save()
        log.write("\nMedtadata has been saved.")
        log.close()
        return "Medtadata has been saved."
    except:
        log.write("\nMedtadata could NOT be saved.")
        log.close()
        return "Medtadata could NOT be saved."

def parse_song(text):
    raw_tags = infobox(text)
    tags = {}

    # Name
    if "Name" in raw_tags:
        tags["title"] = raw_tags["Name"]
    # Artist
    if "Artist" in raw_tags:
        tags["artist"] = raw_tags["Artist"]
    # Album
    if "Album" in raw_tags:
        tags["album"] = raw_tags["Album"]
    elif "from Album" in raw_tags:
        tags["album"] = raw_tags["from Album"]
    # Year
    if "Released" in raw_tags:
        tags["date"] = parse_wiki_date(raw_tags["Released"])
    # Track
    if "track_no" in raw_tags:
        tags["tracknumber"] = raw_tags["track_no"]
    elif tags["album"] != '' and tags["title"] != '':
        print "Looking for track number on album page"
        tags["tracknumber"] = album_track_no(locate_page(tags["album"], "album"),tags["title"])
    # Genre
    if "Genre" in raw_tags:
        tags["genre"] = raw_tags["Genre"]

    return tags

def parse_album(text, song):
    raw_tags = infobox(text)
    tags = {}

    # Name
    tags["title"] = song
    # Album
    if "Name" in raw_tags:
        tags["album"] = raw_tags["Name"]
    # Year
    if "Released" in raw_tags:
        tags["date"] = parse_wiki_date(raw_tags["Released"])
    # Track
        tags["tracknumber"] = album_track_no(text, song)
    # Genre
    if "Genre" in raw_tags:
        tags["genre"] = raw_tags["Genre"]
    
    return tags

def infobox(text):
    pos = "none"
    tags = {}
    tag = ''
    value = ''

    x = 0
    while x < len(text):
        if pos == "none":
            if text[x:x+2] == "| ":
                pos = "tag"
        if pos == "tag":
            if text[x] == "=":
                tag = strip_spaces_from_end(tag[2:])
                pos = "value"
            else:
                tag = tag + text[x]
        if pos == "value":
            if text[x] == "\n":
                tags[tag] = strip_wiki_links(value[2:])
                tag = ''
                value = ''
                pos = "none"
            else:
                value = value + text[x]
        x = x + 1
    return tags

def album_track_no(text, target_song):
    global log

    # Locate track listing
    found = 0
    for x in range(0,len(text)):
        if text[x:x+17] == "==Track listing==" or text[x:x+9] == "==Songs==":
            text = text[x:]
            found = 1
            break
    if found == 0:
        log.write("\nTrack listing could not be found on album page")
        print "Track listing could not be found on album page"
        return ""

    # Find song in track listing
    pos = "none"
    songs = {}
    song = ""
    count = 0
    x = 0
    while x < len(text):
        if pos == "title":
            if text[x] == "\"":
                song = strip_wiki_links(song)
                songs[song] = count
                song = ""
                pos = "none"
            else:
                song = song + text[x]
        if pos == "song":
            if text[x] == "\"":
                pos = "title"
        if pos == "none":
            if text[x:x+2] == "# ":
                pos = "song"
                count = count + 1
                x = x + 2
            elif len(songs) > 0 and text[x:x+2] == "\n\n":
                break
        x = x + 1
    try:
        return str(songs[target_song])
    except:
        log.write("\nSong could not be found on album page")
        print "Song could not be found on album page"
        return ""
    

def page_text(title):
    global log
    # Get page text from a title
    site = wikipedia.getSite('en', 'wikipedia')
    page = wikipedia.Page(site, title)
    try:
        text = page.get(get_redirect = True)
    except wikipedia.NoPage:
        return "NoPage"

    # Get ride of non-ascii characters
    stripped = ''
    removed = []
    for x in range(0,len(text)):
        try:
            char = text[x].encode("ascii")
            stripped = stripped + char
        except:
            removed.append(text[x])
    text = stripped

    # Redirect
    if text[:9] in ['#redirect', '#REDIRECT']:
        title = strip_wiki_links(text[11:-2])
        log.write("\nRedirecting to \"" + title + "\"")
        print "Redirecting to \"" + title + "\""
        text = page_text(title)

    return text

def locate_page(title, target_type):
    global log

    log.write("\nLooking up \"" + title + "\"")
    print "Looking up \"" + title + "\""
    
    text = page_text(title)
    if text == "NoPage":
        return "NoPage"

    # Check if we have the right page type (song, album, etc.)
    type = page_type(text)
    if target_type != type:
        text = locate_page(title + " (" + target_type + ")", target_type)

    # If we still can't find the page, check for a soundtrack
    if text == "NoPage" and target_type == "album" and "Soundtrack" not in title:
        text = locate_page(title + " Soundtrack", "album")

    return text

def page_type(text):
    type = 'unknown'
    for x in range(0,100):
        if text[x:x+16] in ["{{Single infobox", "{{Single Infobox", "{{Infobox single", "{{Infobox Single"]:
            type = "song"
            break
        if text[x:x+15] == "{{Infobox Album":
            type = "album"
            break
    return type

def list_to_string(list):
    string = ''
    for x in list:
        string = string + x
    return string

def string_to_list(string):
    list = []
    for x in string:
        list.append(x)
    return list

def strip_spaces_from_end(string):
    list = string_to_list(string)
    x = 0
    while len(list) > 0:
        if list[-1] == " ":
            del list[-1]
        else:
            break
    return list_to_string(list)

def strip_wiki_links(string):
    list = string_to_list(string)
    x = 0
    out = []
    while x < len(list):
        if list[x] == "[" or list[x] == "]":
            del list[x]
        else:
            x = x + 1
    return list_to_string(strip_double_links(list))

def strip_double_links(list):
    x = 0
    while x < len(list):
        if list[x] == "|":
            del list[:x+1]
            x = 0
        else:
            x = x + 1
    return list

def parse_wiki_date(string):
    list = string_to_list(string)
    x = 1
    while x <= len(list):
        if list[-x] in ['0','1','2','3','4','5','6','7','8','9']:
            if x == 1:
                list = list[-(x+3):]
            else:
                list = list[-(x+3):-(x-1)]
            break
        x = x + 1
    return list_to_string(list)
