
# # # Make sure we have a place to store our cache

init 50 python:
    import os

    if not os.path.isdir(ytm_globals.YT_SIG_DIRECTORY):
        try:
            os.makedirs(ytm_globals.YT_SIG_DIRECTORY)

        except Exception as e:
            # There's nothing that can create the folder during this
            # Which means it has to be a perm issue
            store.ytm_utils.writeLog("Missing folder. Failed to create folder.", e)

# # # "GLOBALS" STUFF

init -5 python in ytm_globals:
    import re

    # Did we check the connection this sesh?
    has_connection = None

    # Maximum search results
    SEARCH_LIMIT = 50

    # mas_gen_scrollable_menu() constants
    # (X, Y, W, H)
    SCR_MENU_AREA = (835, 40, 440, 640)
    SCR_MENU_XALIGN = -0.05
    # (prompt, return, italics, bold, offset)
    SCR_MENU_LAST_ITEMS = (
        ("I changed my mind.", "_changed_mind", False, False, 20),
        ("I want to find another song.", "_another_song", False, False, 0)
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

    PARSE_PATTERN_SCRIPT_BLOCK = re.compile(
        r"(?:window\[\"ytInitialData\"\])(.+?)(?:window\[\"ytInitialPlayerResponse\"\])",
        re.DOTALL
    )
    PARSE_PATTERN_VIDEO = re.compile(
        r"(?:},\"title\":{\"runs\":\[{\"text\":\")(.+?)(?:\"}\],\"accessibility\":)(?:.+?)(?:\"webCommandMetadata\":{\"url\":\"/)(watch\?v=[-_0-9a-zA-Z]{11})(?:\",\"webPageType\":\"WEB_PAGE_TYPE_WATCH\")"
    )
    # PARSE_PATTERN_PLAYLIST = re.compile(r'"playlistVideoRenderer":\{"videoId":"([-_0-9a-zA-Z]{11})","thumbnail"')

    # We keep cache here
    GAME_DIR = renpy.config.gamedir.replace("\\", "/")
    SHORT_MUSIC_DIRECTORY = "/Submods/YouTube Music/temp/"
    FULL_MUSIC_DIRECTORY = GAME_DIR + SHORT_MUSIC_DIRECTORY
    YT_SIG_DIRECTORY = FULL_MUSIC_DIRECTORY + "/youtube-sigfuncs/"
    # Cache extension
    EXTENSION = ".cache"

    # Did we just start a loop or we're continuing looping?
    first_pass = True
    # a dict with the title and path to the audio we need to queue
    audio_to_queue = {"TITLE": "", "PATH": ""}
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

init python in ytm_utils:
    import store
    import store.ytm_globals as ytm_globals
    import os
    import urllib2
    import re
    import pafy
    # from bs4 import BeautifulSoup
    from bs4 import UnicodeDammit
    from HTMLParser import HTMLParser
    # from json import load as to_json

# # # UTIL STUFF

    def writeLog(msg, e=None):
        """
        Writes exceptions in logs

        IN:
            msg - additional info
            e - exception
                (Default: None)
        """
        if e is None:
            e = "Unknown"
        store.mas_utils.writelog(
            "[YTM ERROR]: {0} Exception: {1}\n".format(
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

# # # URL STUFF

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

            # extra handling for the Too Many Requests response
            except urllib2.HTTPError as e:
                if e.code == 429:
                    ytm_globals.has_connection = True
                else:
                    writeLog("No connection.", e)
                    ytm_globals.has_connection = False

            except Exception as e:
                writeLog("No connection.", e)
                ytm_globals.has_connection = False

        return ytm_globals.has_connection

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
        if "/www.youtube.com/" in string or "/youtu.be/" in string:
            return True
        return False

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
        if "list=" in string:
            return True
        return False

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
        return True if "https://" in string else False

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
            ready to use YouTube URL with the search request
        """
        return ytm_globals.YOUTUBE + ytm_globals.SEARCH + toSearchString(string)

    def requestHTML(url):
        """
        Tries to open the given URL and get html

        IN:
            url - a URL to open

        RETURNS:
            html data
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
        NOTE: Won't rise exceptions even if it fails.

        IN:
            html - dirty html data that we're clearing

        RETURNS:
            potentially clear html data
        """
        html_parser = HTMLParser()

        return html_parser.unescape(UnicodeDammit.detwingle(html))

# # # VIDEO STUFF

    def getSearchResults(html):
        """
        Gets a list of search results from the html

        IN:
            html - the html we get videos from

        RETURNS:
            list with tuples (video's title, video's URL)
        """
        videos_info = list()

        if not html:
            return videos_info

        try:
            # bs = BeautifulSoup(clearHTML(html), "html.parser")
            html = clearHTML(html)
        except Exception as e:
            writeLog("Failed to parse html data. Bad encoding?", e)
            return videos_info

        # OUTDATED
        # for data in bs.find_all("a", {"class":"yt-uix-tile-link yt-ui-ellipsis yt-ui-ellipsis-2 yt-uix-sessionlink"}):
        #     # damn youtube's mixes
        #     if (
        #         not "&list=" in data["href"]
        #         and not "/user" in data["href"]
        #         and not "/channel" in data["href"]
        #         # "/watch?v=" in data["href"]
        #     ):
        #         videos_info.append(
        #             (
        #                 re.sub("[\[\]\~\{\}\"\']", "", data["title"]),
        #                 store.ytm_globals.YOUTUBE + data["href"]
        #             )
        #         )

        #         total += 1
        #         if total >= limit:
        #             break

        # I'm not gonna do this shit, youtube. No way.
        # jdata["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][-2]["videoRenderer"]["title"]["runs"][0]["text"]

        # get the block of html we need
        script_block = re.search(ytm_globals.PARSE_PATTERN_SCRIPT_BLOCK, html)
        total_songs = 0

        if script_block is not None:
            # get pairs of title + url
            data = re.findall(ytm_globals.PARSE_PATTERN_VIDEO, script_block.group())

            for title, url in data:
                if (
                    title is not None
                    and url is not None
                ):
                    videos_info.append(
                        (
                            # NOTE: this might be faster than regex
                            title.replace("[", "[[").replace("{", "{{").replace("\\\"", "\""),
                            ytm_globals.YOUTUBE + url
                        )
                    )
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
                bool(video_info[1] not in ytm_globals.audio_history),
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
        return True if "manifest" in stream.url else False

    def fixStreamURL(stream):
        """
        Parses XML manifest to find an appropriate URL to the stream

        IN:
            stream - a stream whose manifest we will parse

        RETURNS:
            pure URL or None if got an exception
        """
        request = urllib2.Request(
            url=stream.url,
            headers=ytm_globals.HEADERS
        )
        try:
            xml = urllib2.urlopen(request, timeout=15).read()
        except Exception as e:
            writeLog("Failed to request XML data.", e)
            return None

        return xml.split('codecs="opus"', 1)[1].split("<BaseURL>", 1)[1].split("</BaseURL>")[0]

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
        try:
            video = pafy.new(
                url=url,
                ydl_opts={"cachedir": ytm_globals.FULL_MUSIC_DIRECTORY}
            )
            stream = video.getbestaudio(preftype="webm")
        except Exception as e:
            writeLog("Failed to request audio stream.", e)
            return None

        # sanity check
        # when trying to get the stream for a live stream, pafy will return None
        if stream is None:
            writeLog("Audio stream is NoneType. Live streams are not supported.")
            return None

        # fix stream if youtube fooked up
        if isBadStream(stream):
            # NOTE: Technically we can get False instead of the URL
            url_to_audio = fixStreamURL(stream)
        else:
            url_to_audio = stream.url

        # make a request
        request = urllib2.Request(
            url=url_to_audio,
            headers=ytm_globals.HEADERS
        )

        # get size
        try:
            # NOTE: yt sends str, need to convert
            content_size = int(
                urllib2.urlopen(request, timeout=15).info().getheaders("Content-Length")[0]
            )
        except Exception as e:
            writeLog("Failed to request content size.", e)
            return None

        return {"TITLE": video.title, "ID": video.videoid, "URL": url_to_audio, "SIZE": content_size}

    def shouldCacheFirst(audio_size):
        """
        Decides if we need to cache the audio on disk before playing it

        IN:
            audio_size - audio size

        RETURNS:
            True if we need to cache it before playing
            False otherwise
        """
        # limit = persistent._ytm_audio_size_limit * 1048576
        limit = ytm_globals.AUDIO_SIZE_LIMIT
        return True if audio_size > limit else False

    def findCache(audio_id):
        """
        Looks for cache on disk

        IN:
            audio_id - audio id (since we use it as a name for cache)

        RETURNS:
            filepath to the cache if we already have it (even if it's small)
            or False if found nothing
        """
        directory = ytm_globals.FULL_MUSIC_DIRECTORY + audio_id + ytm_globals.EXTENSION

        return directory if os.path.isfile(directory) else False

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
        # NOTE: I could generate a name instead of using "Unknown"
        return store.AudioData(_bytes, name)

    def cacheDataToRAM(url, content_size):
        """
        Caches data in RAM to use it right away
        TODO: Can I merge both functions into 1? ¯\_(ツ)_/¯

        IN:
            url - a url to the data
            content_size - the data's size

        RETURNS:
            cache if we successfully downloaded it, False if got an exception
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
            cache if we successfully downloaded it, False if got an exception
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
            return None

        return True

    def playAudio(audio, name=None, clear_queue=True, channel="music"):
        """
        Plays audio files/data

        IN:
            audio - an audio file (can be a list of files too)
            name - the name of the audio. If None, 'YouTube Music' will be used
                (Default: None)
            clear_queue - True clears the queue and play audio, False adds to the the end
                (Default: True)
            channel - the RenPy audio channel we will play the audio in
                (Default: "music")

        OUT:
            True if we were able to play the audio, False otherwise
        """
        if clear_queue:
            renpy.music.stop(channel, 2)
            if name is not None:
                store.songs.current_track = name
            else:
                store.songs.current_track = "YouTube Music"
            store.songs.selected_track = store.songs.FP_NO_SONG
            store.persistent.current_track = store.songs.FP_NO_SONG

        try:
            renpy.music.queue(
                filenames=audio,
                channel=channel,
                loop=True,
                clear_queue=clear_queue,
                fadein=2,
                tight=False
            )

        except Exception as e:
            writeLog("Failed to play audio.", e)
            return False

        else:
            ytm_globals.is_playing = True
            return True

        finally:
            try:
                store.persistent._seen_audio.pop(audio)
            except:
                pass

# # # THREADING STUFF

init 5 python in ytm_threading:
    import store
    import store.ytm_globals as ytm_globals
    import store.ytm_utils as ytm_utils
    import store.mas_threading as mas_threading

    def _search_th(raw_search_request):
        """
        A func we use in threading to get search results

        IN:
            raw_search_request - the user's search request

        RETURNS:
            videos data
        """
        return ytm_utils.getSearchResults(
            ytm_utils.requestHTML(
                ytm_utils.toSearchURL(
                    raw_search_request
                )
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
            ytm_globals.audio_to_queue["TITLE"] = title
            # NOTE: The play function uses short paths so we need to cut a part of the path here
            ytm_globals.audio_to_queue["PATH"] = directory.split(renpy.config.gamedir.replace("\\", "/"), 1)[1]
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
