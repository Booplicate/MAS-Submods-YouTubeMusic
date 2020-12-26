
# # # Startup checks

init 50 python:
    import os

    # Make the folders if needed
    if not os.path.isdir(ytm_globals.YT_SIG_DIRECTORY):
        try:
            os.makedirs(ytm_globals.YT_SIG_DIRECTORY)

        except Exception as e:
            # There's nothing that would create the folder now,
            # which means it has to be a perm issue
            store.ytm_utils.writeLog("Missing the cache folder. Failed to create a folder.", e)

    # Check connection on startup
    ytm_utils.isOnline()

# # # "GLOBALS" STUFF

init -5 python in ytm_globals:
    import re

    # Did we check the connection this sesh?
    has_connection = None

    # Maximum search results
    SEARCH_LIMIT = 50

    # The number of attempts to request audio streams before giving up
    STREAM_REQUEST_ATTEMPTS = 3

    # mas_gen_scrollable_menu() constants
    # (X, Y, W, H)
    SCR_MENU_AREA = (835, 40, 440, 528)
    SCR_MENU_XALIGN = -0.05
    # (prompt, return, italics, bold, offset)
    SCR_MENU_LAST_ITEMS = (
        ("I want to find another song.", "_another_song", False, False, 20),
        ("I changed my mind.", "_changed_mind", False, False, 0),
    )

    # Maximum audio size to play from RAM (bytes)
    AUDIO_SIZE_LIMIT = 15 * 1048576
    # Maximum chunk size to request from yt (bytes)
    REQUEST_CHUNK = 10485760
    # Maximum chunk size for writing data (bytes)
    WRITING_CHUNK = 262144

    # Url parts
    GOOGLE = "http://www.google.com/"
    YOUTUBE = "https://www.youtube.com/"
    SEARCH = "results?search_query="
    WATCH = "watch?v="
    # FILTER_VIDEO = "&sp=EgIQAQ%253D%253D"

    HEADERS = {
        # Mozilla/5.0 (Windows NT 6.1; Win64; x64)
        "User-Agent": "Just Monika! (Monika After Story v{0})".format(renpy.config.version),
        "Accept-Language": "en-US",
        "Content-Language": "en-US",
        "Accept-Charset": "utf8"
    }

    # PARSE_PATTERN_SCRIPT_BLOCK = re.compile(
    #     r"(?:var\s+ytInitialData\s*=\s*|window\[\"ytInitialData\"\]|scraper_data_begin)(.+?)(?:ytInitialPlayerResponse|window\[\"ytInitialPlayerResponse\"\]|scraper_data_end)",
    #     re.DOTALL
    # )
    # PARSE_PATTERN_VIDEO = re.compile(
    #     r"(?:},\"title\":{\"runs\":\[{\"text\":\")(.+?)(?:\"}\],\"accessibility\":)(?:.+?)(?:\"webCommandMetadata\":{\"url\":\"/)(watch\?v=[-_0-9a-zA-Z]{11})(?:\",\"webPageType\":\"WEB_PAGE_TYPE_WATCH\")"
    # )
    # PARSE_PATTERN_PLAYLIST = re.compile(r'"playlistVideoRenderer":\{"videoId":"([-_0-9a-zA-Z]{11})","thumbnail"')

    # We keep cache here
    GAME_DIR = renpy.config.gamedir.replace("\\", "/")
    SHORT_MUSIC_DIRECTORY = "/Submods/YouTube Music/temp/"
    FULL_MUSIC_DIRECTORY = GAME_DIR + SHORT_MUSIC_DIRECTORY
    YT_SIG_DIRECTORY = FULL_MUSIC_DIRECTORY + "/youtube-sigfuncs/"
    # Cache extension
    EXTENSION = ".cache"

    # Params for yt-dl
    # NOTE: these might be interesting:
    #   nocheckcertificate
    #   prefer_insecure
    YDL_OPTS = {
        # Redirect the cache to our folder (youtube-sigfuncs will be created automatically)
        "cachedir": FULL_MUSIC_DIRECTORY,
        # "verbose": True,
        # RenPy has broken stdio, we better not to use it
        "quiet": True,
        # NOTE: this probably doesn't work
        "user_agent": HEADERS["User-Agent"],
    }

    # Did we just start a loop or we're continuing looping?
    first_pass = True
    # a dict with the title and path to the audio we need to queue
    audio_to_queue = {"title": "", "path": ""}
    # Do we play an audio or no
    is_playing = False
    # all videos URLs from the playlist we're currently listening to
    # playlist = []
    # id of the current track from the playlist
    # current_song_from_playlist = 0
    # a list of search requests, no dupes
    search_history = []
    # a list of played audio (youtube ids), no dupes
    audio_history = []

init python in ytm_screen_utils:
    import store

    class YTMInputValue(store.InputValue):
        """
        Our subclass of InputValue for internal use
        Allows us to manipulate the user input
        For more info read renpy docs (haha yeah...docs...renpy...)
        """
        def __init__(self):
            self.default = True
            self.input_value = ""
            self.editable = True
            self.returnable = True

        def get_text(self):
            return self.input_value

        def set_text(self, s):
            if not isinstance(s, basestring):
                s = unicode(s)
            self.input_value = s

    def toggleChildScreenAnimation(new_value):
        """
        This allows us to hide the sub-menu w/o animation
        when we need it to just disappear immediately

        IN:
            new_value - a bool to switch the setting
        """
        _screen = renpy.get_screen("ytm_history_submenu")
        if _screen:
            _settings = _screen.scope.get("settings", None)
            if _settings:
                _settings["animate"] = new_value

    def setParentInputValue(new_input):
        """
        A wrapper which allows us to do the magic in local env

        IN:
            new_input - a new value for input
        """
        _screen = renpy.get_screen("ytm_input_screen")
        if _screen:
            ytm_input = _screen.scope.get("ytm_input", None)
            if ytm_input:
                ytm_input.set_text(new_input)

init python in ytm_utils:
    import store
    import store.ytm_globals as ytm_globals
    import os
    import urllib2
    import re
    # import pafy
    import youtube_dl
    # from bs4 import BeautifulSoup
    from bs4 import UnicodeDammit
    from HTMLParser import HTMLParser
    # from json import load as to_json
    from time import time
    from threading import Thread

    youtube_dl.std_headers["User-Agent"] = ytm_globals.YDL_OPTS["user_agent"]

# # # UTIL STUFF

    def writeLog(msg, e=None):
        """
        Writes exceptions in logs

        IN:
            msg - additional info
            e - exception
                (Default: None)
        """
        if e is not None:
            e = " Exception: {0}".format(e)
            if not e.endswith("."):
                e += "."

        else:
            e = ""

        store.mas_submod_utils.writeLog(
            "[YTM ERROR]: {0}{1}\n".format(
                msg,
                e
            )
        )

    def deleteFiles(path, extension, e_str=None):
        """
        Does what Monika does the best

        IN:
            path - the path we're deleting files in
            extension - the extension files should have in order to get deleted
            e_str - the message we log along with the exception (if one occurs)
                if None, will use an empty string
                (Default: None)
        """
        try:
            for file in os.listdir(path):
                if (
                    os.path.isfile(path + file)
                    and file.endswith(extension)
                ):
                    os.remove(path + file)

        except Exception as e:
            if not e_str:
                e_str = ""
            writeLog(e_str, e)

    def deleteCache():
        """
        Deletes the cache
        """
        renpy.music.stop("music", 1)

        deleteFiles(
            ytm_globals.FULL_MUSIC_DIRECTORY,
            ytm_globals.EXTENSION,
            "Couldn't remove cache."
        )

    def deleteSignatures():
        """
        Deletes youtube signatures
        """
        deleteFiles(
            ytm_globals.YT_SIG_DIRECTORY,
            ".json",
            "Couldn't remove signatures."
        )

    def cleanUp():
        """
        Makes it so you can't call my submod a bloatware
        """
        deleteCache()
        deleteSignatures()

    def fixPersistent():
        """
        Func to clean persistent from AudioData objects,
        so if someone somehow got the bad data in their persistent,
        we can easily remove these bits
        """
        for audio in reversed(store.persistent._seen_audio.keys()):
            if isinstance(audio, store.AudioData):
                store.persistent._seen_audio.pop(audio)
                writeLog("Found bad data in persistent and removed it.")

    def addSearchHistory(entry):
        """
        Adds the given entry to the search history list
        Will update the list if the entry is already in it

        IN:
            entry - an entry to add
        """
        # since we use this in buttons prompts, we need to "sanitize" it
        entry = (
            entry[0].replace("[", "[[").replace("{", "{{"),
            entry[1]
        )

        if entry in ytm_globals.search_history:
            ytm_globals.search_history.remove(entry)
        ytm_globals.search_history.append(entry)

    def addAudioHistory(entry):
        """
        Adds the given entry to the audio history list
        Will update the list if the entry is already in it

        IN:
            entry - an entry to add
        """
        if entry in ytm_globals.audio_history:
            ytm_globals.audio_history.remove(entry)
        ytm_globals.audio_history.append(entry)

    def isOnline(force_update=False):
        """
        Checks if we have an internet connection

        RETURNS:
            True if we do,
            False otherwise
        """
        if (
            force_update
            or not ytm_globals.has_connection
        ):
            try:
                request = urllib2.Request(
                    url=ytm_globals.GOOGLE,
                    headers=ytm_globals.HEADERS
                )
                urllib2.urlopen(
                    request,
                    timeout=15
                )
                ytm_globals.has_connection = True

            except Exception as e:
                # Extra handling for the Too Many Requests response
                if isinstance(e, urllib2.HTTPError) and e.code == 429:
                    ytm_globals.has_connection = True

                else:
                    writeLog("No connection.", e)
                    ytm_globals.has_connection = False

        return ytm_globals.has_connection

    def clean_string(string):
        """
        Cleans a video title

        IN:
            string - string to handle

        OUT:
            clean string
        """
        # Clean the string
        string = string.replace("[", "[[").replace("{", "{{").replace("\\\"", "\"").encode(errors="replace")
        # Workaround if we get a title longer than 100 chars (somehow?)
        if len(string) > 100:
            string = string[:95] + "(...)"

        return string

# # # URL STUFF

    def isYouTubeURL(string):
        """
        Checks if the given string is a YouTube URL
        TODO: more checks to make sure the user gave a usable url

        IN:
            string - a string to check

        RETURNS:
            True if it's a YouTube URL,
            False if it is not
        """
        return ("/www.youtube.com/" in string or "/youtu.be/" in string)

    def isPlaylistURL(string):
        """
        Checks if the given string is a URL to a playlist

        IN:
            string - a string to check

        ASSUMES:
            we checked the string in isYouTubeURL

        RETURNS:
            True if it's a URL to a playlist,
            False otherwise
        """
        return "list=" in string

    def isSafeURL(string):
        """
        Checks if the given string is a safe URL
        NOTE: UNUSED

        IN:
            string - a string to check

        RETURNS:
            True if safe URL,
            False otherwise
        """
        return "https://" in string

    def makeSafeURL(string):
        """
        Tries to make a safe URL from the given string
        NOTE: UNUSED

        IN:
            string - the string we're trying to fix

        RETURNS:
            safe to use URL, will return the base string if it's already in the appropriate format
        """
        if "http://" in string:
            return string.replace("http://", "https://", 1)

        elif "https://" in string:
            return string

        else:
            return "https://" + string

    def toSearchString(string):
        """
        Converts user's raw input to a formatted string ready to use in the URL

        IN:
            string - the string we are trying to format

        RETURNS:
            formatted string
        """
        return re.sub("\s+", "+", re.sub("[^ a-zA-Z!_№~`\"\'\d\(\)\^\*\\-]", "", string))

    def toSearchURL(string):
        """
        Merges URLs' parts with user's request

        IN:
            string - the user's search request

        RETURNS:
            youTube URL with the search query
            or empty string if the request was empty
        """
        string = toSearchString(string)
        if string:
            return ytm_globals.YOUTUBE + ytm_globals.SEARCH + string
        return ""

    def requestHTML(url):
        """
        Tries to open the given URL and get html

        IN:
            url - a URL to open

        RETURNS:
            html data, or None if got an exception
        """
        request = urllib2.Request(
            url=url,
            headers=ytm_globals.HEADERS
        )
        try:
            html = urllib2.urlopen(request, timeout=15).read()
        except Exception as e:
            writeLog("Failed to request HTML data.", e)
            return None

        return html

    def clearHTML(html):
        """
        Tries to clear html up from weird symbol and encodings

        IN:
            html - dirty html data that we're clearing

        RETURNS:
            potentially clear html data
        """
        html_parser = HTMLParser()
        return html_parser.unescape(UnicodeDammit.detwingle(html))

# # # VIDEO STUFF

    def getSearchResults(search_request):
        """
        Gets a list of search results

        IN:
            search_request - search request

        RETURNS:
            list with tuples (video's title, video's URL)
        """
        videos_info = list()

        if not search_request:
            return videos_info

        with youtube_dl.YoutubeDL(dict(ytm_globals.YDL_OPTS)) as yt_dl:
            try:
                # Try to get basic info for the first 99 videos
                yt_dl_info = yt_dl.extract_info(
                    "ytsearch{0}:{1}".format(ytm_globals.SEARCH_LIMIT, search_request),
                    download=False,
                    process=False
                )

            except Exception as e:
                writeLog("Failed to retrieve search results.", e)
                return videos_info

            # This probably cannot be None nor even empty, but just in case
            if not yt_dl_info:
                writeLog("Got invalid data from yt-dl: {0}".format(yt_dl_info))
                return videos_info

            # NOTE: This may contain a generator
            entries = yt_dl_info.get("entries", [])
            total_songs = 0
            for entry in entries:
                title = entry.get("title", "[An untitled video]")
                id = entry.get("id", entry.get("url", None))

                # If we couldn't get the id, we should skip this video
                if id is None or len(id) != 11:
                    writeLog("Got invalid video id: {0}".format(id))
                    continue

                # Sanitize the title so we can display it
                if title:
                    title = clean_string(title)
                url = ytm_globals.YOUTUBE + ytm_globals.WATCH + id

                videos_info.append((title, url))
                total_songs += 1
                if total_songs >= ytm_globals.SEARCH_LIMIT:
                    return videos_info

        return videos_info

    def buildMenuList(videos_info):
        """
        Builds a list to use in mas_gen_scrollable_menu()

        IN:
            videos_info - a list of tuples with titles and URLs for the menu

        RETURNS:
            ready to use menu list for mas_gen_scrollable_menu
        """
        if not videos_info:
            return []

        return [
            (
                video_info[0],
                video_info[1],
                (video_info[1] not in ytm_globals.audio_history),
                False
            )
            for video_info in videos_info
        ]

    def getVideosFromPlaylist(url):
        """
        Gets a list of videos in a playlist from the given URL
        NOTE: I'm not sure, but this might be limited
            to only 200 videos by youtube
        NOTE: UNUSED

        IN:
            url - a url to a playlist

        RETURNS:
            list with videos URLs from the playlist
        """
        # we need a direct url to the playlist
        if "/playlist?" not in url:
            url = re.sub(r"watch\?v=([-_0-9a-zA-Z]{11})\&", "playlist?", url)

        # get the html
        dirty_html = requestHTML(url)
        if not dirty_html:
            return []

        html = clearHTML(dirty_html)

        # define the pattern
        pattern = re.compile(r'"playlistVideoRenderer":\{"videoId":"([-_0-9a-zA-Z]{11})","thumbnail"')
        # look for videos ids in the html by the pattern
        ids_list = re.findall(pattern, html)
        # use list compr to turn ids into urls
        return [ytm_globals.YOUTUBE + "watch?v=" + id for id in ids_list]

# # # AUDIO STUFF

    def isBadStream(stream):
        """
        Checks if youtube fooked up once again

        IN:
            stream - a stream we will check

        RETURN:
            True - fooked up, False - we are good
        """
        return "manifest" in stream.url

    def fixStreamURL(stream_url):
        """
        Parses XML manifest to find an appropriate URL to the stream

        IN:
            stream - a stream whose manifest we will parse

        RETURNS:
            pure URL or None if got an exception
        """
        request = urllib2.Request(
            url=stream_url,
            headers=ytm_globals.HEADERS
        )
        try:
            xml = urllib2.urlopen(request, timeout=15).read()
            proper_url = xml.split('codecs="opus"', 1)[1].split("<BaseURL>", 1)[1].split("</BaseURL>")[0]
            if "ratebypass" not in proper_url:
                proper_url += "&ratebypass=yes"

            return proper_url

        except Exception as e:
            writeLog("Failed to request XML data.", e)

        return None

    def getAudioInfo(url):
        """
        Gets the best audio stream for the video from the given URL
        and some other info as well

        IN:
            url - video's URL

        RETURNS:
            dict with the title, id, link to the audio stream and its size
            or None if we got an exception
        """
        tries = ytm_globals.STREAM_REQUEST_ATTEMPTS
        err_types = set()
        while tries > 0:
            tries -= 1
            try:
                with youtube_dl.YoutubeDL(dict(ytm_globals.YDL_OPTS)) as yt_dl:
                    yt_dl_info = yt_dl.extract_info(url, download=False)

                    # Get list of dicts
                    formats = yt_dl_info.get("formats", [])
                    if not formats:
                        writeLog("Got empty audio data from yt-dl.")
                        return None

                    # Now filter so we get the best format that works in renpy
                    best_format = max(formats, key=lambda frm: (frm.get("acodec") == "opus", frm.get("abr"), frm.get("asr")))
                    if best_format.get("acodec") != "opus":
                        writeLog("No audio streams with opus codec found.")
                        return None

                    title = clean_string(yt_dl_info.get("title", "[An untitled video]"))

                    id = yt_dl_info.get("id", yt_dl_info.get("url", None))
                    if id is None or len(id) != 11:
                        writeLog("Got invalid video id from yt-dl: {0}".format(id))
                        return None

                    content_size = None
                    stream_url = best_format.get("url")
                    if not stream_url:
                        if stream_url is None:
                            writeLog("Audio stream is NoneType. Live streams are not supported yet.")

                        else:
                            writeLog("Got invalid stream url from yt-dl: {0}.".format(stream_url))
                        return None

                    elif "manifest" in stream_url:
                        stream_url = fixStreamURL(stream_url)
                        if not stream_url:
                            writeLog("Failed to get stream url from manifest.")
                            return None

                    # If we got a propen stream url, then we assume a proper content size
                    else:
                        content_size = best_format.get("filesize")

                    # Fallback if we got the wrong stream, or yt-dl couldn't return the CS
                    if not content_size:
                        try:
                            content_size = int(
                                urllib2.urlopen(
                                    urllib2.Request(
                                        url=stream_url,
                                        headers=ytm_globals.HEADERS
                                    ),
                                    timeout=15
                                ).info().getheaders("Content-Length")[0]
                            )

                        except Exception as e:
                            writeLog("Failed to request content size.", e)
                            return None

            except Exception as e:
                e_type = type(e)
                if e_type not in err_types:
                    err_types.add(e_type)
                    writeLog("Failed to request audio stream.", e)

                if tries <= 0:
                    return None

            else:
                # If we got the stream w/o exceptions, break the loop
                tries = 0

        return {"title": title, "id": id, "url": stream_url, "size": content_size}

    def shouldCacheFirst(audio_size):
        """
        Decides if we need to cache the audio on disk before playing it

        IN:
            audio_size - audio size

        RETURNS:
            True if we need to cache it before playing
            False otherwise
        """
        return audio_size > ytm_globals.AUDIO_SIZE_LIMIT

    def findCache(audio_id):
        """
        Looks for cache on disk

        IN:
            audio_id - audio id (since we use it as a name for cache)

        RETURNS:
            True if found,
            False otherwise
        """
        directory = ytm_globals.FULL_MUSIC_DIRECTORY + audio_id + ytm_globals.EXTENSION
        return os.path.isfile(directory)

    def bytesToAudioData(_bytes, name="Unknown"):
        """
        Converts stream of bytes into AudioData obj which can be played
        via renpy's audio system

        IN:
            _bytes - a stream of bytes we will convert
            name - a name to use for that object
                (Default: "Unknown")

        RETURNS:
            AudioData object
        """
        return store.AudioData(_bytes, name)

    def cacheDataToRAM(url, content_size):
        """
        Caches data in RAM to use it right away
        TODO: Can I merge both functions into 1? ¯\_(ツ)_/¯

        IN:
            url - a url to the data
            content_size - the data's size

        RETURNS:
            cache if we successfully downloaded it, None if got an exception
        """
        cache = b""
        bottom_bracket = 0
        top_bracket = ytm_globals.REQUEST_CHUNK
        headers = dict(ytm_globals.HEADERS)
        headers.update({"Range": "bytes={0}-{1}".format(bottom_bracket, top_bracket)})

        try:
            # TODO: should have this part only once
            request = urllib2.Request(url=url, headers=headers)
            response = urllib2.urlopen(request, timeout=15)

            while True:
                cache_buffer = response.read(ytm_globals.WRITING_CHUNK)

                if not cache_buffer:
                    break

                cache += cache_buffer
                cache_size = len(cache)

                if (
                    cache_size == top_bracket
                    and not cache_size == content_size
                ):
                    bottom_bracket = top_bracket
                    top_bracket += ytm_globals.REQUEST_CHUNK
                    headers["Range"] = "bytes={0}-{1}".format(bottom_bracket, top_bracket)
                    request = urllib2.Request(url=url, headers=headers)
                    response = urllib2.urlopen(request, timeout=15)

        except Exception as e:
            writeLog("Failed to cache audio data.", e)
            return None

        return cache

    def cacheDataToDisk(url, content_size, directory):
        """
        Caches data on disk to use it later
        TODO: Can I merge both functions into 1? ¯\_(ツ)_/¯

        IN:
            url - a url to the data
            content_size - the data's size
            directory - the directory we are going to save the cache to
                NOTE: should include the file's name

        RETURNS:
            cache if we successfully downloaded it, None if got an exception
        """
        cache_size = 0
        bottom_bracket = 0
        top_bracket = ytm_globals.REQUEST_CHUNK
        headers = dict(ytm_globals.HEADERS)
        headers.update({"Range": "bytes={0}-{1}".format(bottom_bracket, top_bracket)})

        try:
            request = urllib2.Request(url=url, headers=headers)
            response = urllib2.urlopen(request, timeout=15)

            with open(directory, 'wb') as audio_cache:
                while True:
                    cache_buffer = response.read(ytm_globals.WRITING_CHUNK)

                    if not cache_buffer:
                        break

                    cache_size += len(cache_buffer)
                    audio_cache.write(cache_buffer)

                    if (
                        cache_size == top_bracket
                        and not cache_size == content_size
                    ):
                        bottom_bracket = top_bracket
                        top_bracket += ytm_globals.REQUEST_CHUNK
                        headers["Range"] = "bytes={0}-{1}".format(bottom_bracket, top_bracket)
                        request = urllib2.Request(url = url, headers=headers)
                        response = urllib2.urlopen(request, timeout=15)

        except Exception as e:
            writeLog("Failed to cache audio data.", e)
            return None

        return directory

    def cacheFromRAM(_bytes, directory):
        """
        Moves the cache from RAM to disk to use it later

        IN:
            _bytes - data we will write
            directory - the directory we are going to save the cache to
                NOTE: should include the file's name

        RETURNS:
            True if successful, False oethrwise
        """
        try:
            with open(directory, 'wb') as audio_cache:
                audio_cache.write(_bytes)
        except Exception as e:
            writeLog("Failed to write cache on disk from RAM.", e)
            return False

        return True

    def playAudio(audio, name=None, loop=True, clear_queue=True, fadein=2, set_ytm_flag=True):
        """
        Plays audio files/data

        IN:
            audio - an audio file (can be a list of files too)
            name - the name of the audio. If None, 'YouTube Music' will be used
                (Default: None)
            loop - whether or not we loop this track
                (Default: True)
            clear_queue - True clears the queue and play audio, False adds to the the end
                (Default: True)
            fadein - fadein for this track in seconds
                (Default: 2)
            set_ytm_flag - whether or not we set the flag that youtube music is playing something
                (Default: True)

        OUT:
            True if we were able to play the audio, False otherwise
        """
        if clear_queue:
            renpy.music.stop("music", 2)
            if name is not None:
                store.songs.current_track = name
            else:
                store.songs.current_track = "YouTube Music"
            store.songs.selected_track = store.songs.FP_NO_SONG
            store.persistent.current_track = store.songs.FP_NO_SONG

        try:
            renpy.music.queue(
                filenames=audio,
                channel="music",
                loop=loop,
                clear_queue=clear_queue,
                fadein=fadein,
                tight=False
            )

        except Exception as e:
            writeLog("Failed to play audio.", e)
            return False

        else:
            ytm_globals.is_playing = set_ytm_flag
            return True

        finally:
            try:
                store.persistent._seen_audio.pop(audio)
            except:
                pass

    def check_o31_spook():
        """
        Checks whether or not we should play an into track for o31
        NOTE: runtime only
        """
        if (
            store.mas_isO31()
            and not store.persistent._mas_o31_in_o31_mode
            # and store.persistent._mas_pm_likes_spoops
            and store.persistent.current_track == store.songs.FP_NO_SONG
            and renpy.music.get_playing() is None
            and not store.songs.hasMusicMuted()
            and store.mas_isMoniHappy(higher=True)
            and store.mas_getEVL_shown_count("ytm_monika_find_music", 0) > 5
            and isOnline()
        ):
            spook_thread = Thread(target=_do_o31_spook)
            spook_thread.daemon = True
            spook_thread.start()

    def _do_o31_spook():
        """
        This mean function spooks you and takes all your candies
        """
        start_ts = time()
        # Credits to T.L.B. Orchestration
        audio_info = getAudioInfo("https://youtu.be/J7XtCHxVUto")
        if audio_info:
            cache = cacheDataToRAM(audio_info["url"], audio_info["size"])
            end_ts = time()
            d_t = end_ts - start_ts
            if cache and d_t < 15:
                playAudio(
                    bytesToAudioData(cache, "Spook~"),
                    name="Spook~",
                    loop=False,
                    fadein=10,
                    set_ytm_flag=False
                )

# # # THREADING STUFF

init 5 python in ytm_threading:
    import store
    import store.ytm_globals as ytm_globals
    import store.ytm_utils as ytm_utils
    import store.mas_threading as mas_threading

    def _search_th(raw_search_request):
        """
        A func we use in threading to get search results and format them to display in the menu

        IN:
            raw_search_request - the user's search request

        RETURNS:
            videos data formatted for the menu
        """
        return ytm_utils.buildMenuList(
            ytm_utils.getSearchResults(
                raw_search_request
            )
        )

    def _play_audio_th(url, video_id, video_title, audio_size, clear_queue):
        """
        Caches small audio and plays it in thread

        IN:
            url - a url to that audio
            video_id - the video's id
            video_title - the video's title
            audio_size - size of the audio
            clear_queue - should we clear the queue or not

        RETURNS:
            cache if we were able to successfully download it and play
            None if got an exception
        """
        cache = ytm_utils.cacheDataToRAM(url, audio_size)
        if cache:
            audio = ytm_utils.bytesToAudioData(cache, "YouTubeID: " + video_id)
            is_playing_audio = ytm_utils.playAudio(audio, name=video_title, clear_queue=clear_queue)

            if is_playing_audio:
                return cache
        # got an exception somewhere
        return None

    def _get_audio_info_th(url):
        """
        Runs getAudioInfo() in thread for better performance

        IN:
            url - the url we will get data from

        RETURNS:
            dict with various data (check getAudioInfo() for more info)
        """
        return ytm_utils.getAudioInfo(url)

    def _cache_from_RAM_th(_bytes, directory):
        """
        Writes bytes from RAM on disk using threading

        IN:
            _bytes - data we will write
            directory - the directory we are going to save the cache to
                NOTE: should include the file's name

        RETURNS:
            True if successful otherwise False
        """
        return ytm_utils.cacheFromRAM(_bytes, directory)

    def _cache_from_URL_th(url, title, content_size, directory):
        """
        Runs cacheDataToDisk() in thread, after downloading the cache
        will push an event so [player] will know we're good

        IN:
            url - a url we will download from
            title - the video's title
            content_size - the data's size
            directory - the directory we are going to save the cache to
                NOTE: should include the file's name

        RETURNS:
            True if we successefully downloaded and queued,
            False if got an exception
        """
        cache = ytm_utils.cacheDataToDisk(url, content_size, directory)
        if cache:
            ytm_globals.audio_to_queue["title"] = title
            # NOTE: The play function uses short paths so we need to cut a part of the path here
            ytm_globals.audio_to_queue["path"] = directory.split(ytm_globals.GAME_DIR, 1)[1]
            store.pushEvent("ytm_monika_finished_caching_audio")
            return True
        # got an exception somewhere
        return False

    def updateThreadArgs(thread, args):
        """
        Sets new args for the thread

        IN:
            thread - a thread we are changing args for
            args - a list of args
        """
        thread._th_args = args

    def resetThread(thread):
        """
        Resets thread properties so we can start another one
        regardless of if it's ready or not

        IN:
            thread - the thread we reset
        """
        thread._th_result = None
        thread._th_done = True
        thread.ready = True

    search_music = mas_threading.MASAsyncWrapper(_search_th)
    get_audio_info = mas_threading.MASAsyncWrapper(_get_audio_info_th)
    play_audio = mas_threading.MASAsyncWrapper(_play_audio_th)
    cache_audio_from_ram = mas_threading.MASAsyncWrapper(_cache_from_RAM_th)
    cache_audio_from_url = mas_threading.MASAsyncWrapper(_cache_from_URL_th)
