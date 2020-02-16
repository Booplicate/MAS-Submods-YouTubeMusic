
# # # "GLOBALS" STUFF

init -15 python in ytm_globals:
    # Did we check the connection this sesh?
    has_connection = None

    # Maximum search results
    SEARCH_LIMIT = 15

    # mas_gen_scrollable_menu() constants
    # (X, Y, W, H)
    MENU_AREA = (835, 40, 440, 640)
    MENU_XALIGN = -0.05
    # (prompt, return, italics, bold, offset)
    MENU_CHANGED_MIND = ("I changed my mind.", "_changed_mind", False, False, 20)
    MENU_ANOTHER_SONG = ("I want to find another song.", "_another_song", False, False, 0)

    # Maximum audio size to play from RAM (bytes)
    AUDIO_SIZE_LIMIT = 15728640
    # Maximum chunk size to request from yt (bytes)
    REQUEST_CHUNK = 10485760
    # Maximum chunk size for writing data (bytes)
    WRITING_CHUNK = 262144

    # Url parts
    YOUTUBE = "https://www.youtube.com/"
    SEARCH = "results?search_query="

    # API key for Google API
    # API_KEY = ""

    # Did we just start a loop or we're continuing looping?
    first_pass = True
    # A path to the audio that we need to queue
    audio_to_queue = ""
    # Do we play an audio or no
    is_playing = False

    # We keep cache there
    SHORT_MUSIC_DIRECTORY = "/Submods/YouTube Music/temp/"
    FULL_MUSIC_DIRECTORY = renpy.config.gamedir.replace("\\", "/") + SHORT_MUSIC_DIRECTORY
    # Cache extension
    EXTENSION = ".cache"

init -10 python:
    import os
    import urllib2
    from re import sub
    import pafy
    from bs4 import BeautifulSoup
    from bs4 import UnicodeDammit
    from HTMLParser import HTMLParser

# # # UTIL STUFF

    def ytm_writeLog(msg, e=None):
        """
        Writes exceptions in logs

        IN:
            msg - additional info
            e - an exception
        """
        store.mas_utils.writelog("[YTM ERROR]: {0} Exception: {1}\n".format(msg, e))

    def ytm_cleanUp():
        """
        Deletes the cache
        """
        path = store.ytm_globals.FULL_MUSIC_DIRECTORY

        try:
            renpy.music.stop("music", 2)
            for trash in os.listdir(path): os.remove(path + trash)
        except Exception as e:
            ytm_writeLog("Couldn't remove cache.", e)

# # # URL STUFF

    def ytm_isOnline():
        """
        Checks if we have an internet connection

        RETURNS:
            True or False
        """
        # return True
        if store.ytm_globals.has_connection is None:
            try:
                urllib2.urlopen("http://www.google.com/", timeout=15)
                store.ytm_globals.has_connection = True
                return store.ytm_globals.has_connection
            except urllib2.URLError as e:
                ytm_writeLog("No connection.", e)
                store.ytm_globals.has_connection = False
                return store.ytm_globals.has_connection

        else:
            return store.ytm_globals.has_connection

    def ytm_isYouTubeURL(string):
        """
        Checks if the given string is a YouTube URL

        IN:
            string - a string to check

        RETURNS:
            True if it's a YouTube URL, False if it is not
        """
        if "/www.youtube.com/" in string or "/youtu.be/" in string:
            return True
        else:
            return False

    def ytm_isSafeURL(string):
        """
        Checks if the given string is a safe URL

        IN:
            string - a string to check

        RETURNS:
            True if safe URL, False otherwise
        """
        return True if "https://" in string else False

    def ytm_makeSafeURL(string):
        """
        Tries to make a safe URL from the given string

        IN:
            string - a string we're trying to fix

        RETURNS:
            a safe to use URL, will return the base string if it's already in an appropriate format
        """
        if "http://" in string:
            return string.replace("http://", "https://", 1)

        elif "https://" in string:
            return string

        else:
            return "https://" + string

    def ytm_toSearchString(string):
        """
        Converts user's raw input to a formatted string ready to use in the URL

        IN:
            string - a string we are trying to format

        RETURNS:
            a formatted string
        """
        return sub("\s+", "+", sub("[^ a-zA-Z!_№~`\"\'\d\(\)\^\*\\-]", "", string))

    def ytm_toSearchURL(string):
        """
        Merges URLs' parts with user's request

        IN:
            string - user's search request

        RETURNS:
            a ready to use YouTube URL with the search request
        """
        return store.ytm_globals.YOUTUBE + store.ytm_globals.SEARCH + ytm_toSearchString(string)

    def ytm_requestHTML(url):
        """
        Tries to open the given URL and get html

        IN:
            url - a URL to open

        RETURNS:
            html data
        """
        headers = {
            # Mozilla/5.0 (Windows NT 6.1; Win64; x64)
            "User-Agent": "Just Monika! (MAS v. %s)" % config.version,
            "Accept-Language": "en-US",
            "Content-Language": "en-US",
            "Accept-Charset": "utf8"
        }
        req = urllib2.Request(url=url, headers=headers)

        try:
            html = urllib2.urlopen(req, timeout=15).read()
        except Exception as e:
            ytm_writeLog("Failed to request HTML data.", e)
            return False

        return html

    def ytm_clearHTML(html):
        """
        Tries to clear html up from weird symbol and encodings
        NOTE: Won't rise exceptions even if it fails.

        IN:
            html - a dirty html data that we're clearing

        RETURNS:
            potentially clear html data
        """
        html_parser = HTMLParser()

        return html_parser.unescape(UnicodeDammit.detwingle(html))

# # # VIDEO STUFF

    def ytm_getSearchResults(html, limit=store.ytm_globals.SEARCH_LIMIT):
        """
        Gets a list of search results from the html

        IN:
            html - an html we get videos from
            limit - maximum amount of videos in the list
                (Default: SEARCH_LIMIT)

        RETURNS:
            a list with tuples (video's title, video's URL)
        """
        videos_info = list()

        if not html:
            return videos_info

        try:
            bs = BeautifulSoup(ytm_clearHTML(html), "html.parser")
        except Exception as e:
            ytm_writeLog("Failed to parse html data. Bad encoding?", e)
            return False

        i = 0
        for data in bs.find_all("a", {"class":"yt-uix-tile-link yt-ui-ellipsis yt-ui-ellipsis-2 yt-uix-sessionlink spf-link"}):
            # damn youtube's mixes
            if (
                not "&list=" in data["href"]
                and not "/user" in data["href"]
                # "/watch?v=" in data["href"]
            ):
                videos_info.append((sub("[\[\]\~\{\}\"\']", "", data["title"]), store.ytm_globals.YOUTUBE + data["href"]))

                i += 1
                if i == limit:
                    break

        return videos_info

    def ytm_buildMenuList(videos_info):
        """
        Builds a list to use in mas_gen_scrollable_menu()

        IN:
            videos_info - a list of tuples with titles and URLs for the menu

        RETURNS:
            a ready to use menu list for mas_gen_scrollable_menu()
        """
        menu_list = list()

        if not videos_info:
            return menu_list

        for video_data in videos_info:
            menu_list.append((video_data[0], video_data[1], False, False))
        # menu_list.append(("I changed my mind.", "_changed_mind", False, True))
        # menu_list.append(("I want to find another song.", "_another_song", False, True))
        return menu_list

# # # AUDIO STUFF

    def ytm_isBadStream(stream):
        """
        Checks if youtube fooked up once again

        IN:
            stream - a stream we will check

        RETURN:
            True - fooked up, False - we are good
        """
        return True if "manifest" in stream.url else False

    def ytm_fixStreamURL(stream):
        """
        Parses XML manifest to find an appropriate URL to the stream

        IN:
            stream - a stream whose manifest we will parse

        RETURNS:
            pure URL or False if got an exception
        """
        try:
            xml = urllib2.urlopen(stream.url, timeout=15).read()
        except Exception as e:
            ytm_writeLog("Failed to request XML data.", e)
            return False

        # return re.split('</BaseURL>', re.split('<BaseURL>', re.split('codecs="opus"', xml, 1)[-1], 1)[-1], 1)[0]
        return xml.split('codecs="opus"', 1)[1].split("<BaseURL>", 1)[1].split("</BaseURL>")[0]

    def ytm_getAudioInfo(url):
        """
        Gets the best audio stream for the video from the given URL
        and some other info as well

        IN:
            url - video's URL

        RETURNS:
            a dict with the title, id, link to the audio stream and its size
            or False if we got an exception
        """
        try:
            video = pafy.new(url)
            stream = video.getbestaudio(preftype="webm")
        except Exception as e:
            ytm_writeLog("Failed to request audio stream.", e)
            return False

        # sanity check
        # when trying to get the stream for a live stream, pafy will return None
        if stream is None:
            ytm_writeLog("Audio stream is NoneType. Live streams are not supported.")
            return False

        if ytm_isBadStream(stream):
            # NOTE: Technically we can get False instead of the URL
            url_to_audio = ytm_fixStreamURL(stream)
        else:
            url_to_audio = stream.url

        try:
            # yt sends str, need to convert
            content_size = int(urllib2.urlopen(url_to_audio).info().getheaders("Content-Length")[0])
        except Exception as e:
            ytm_writeLog("Failed to request content size.", e)
            return False

        return {"TITLE": video.title, "ID": video.videoid, "URL": url_to_audio, "SIZE": content_size}

    def ytm_shouldCacheFirst(audio_size):
        """
        Decides if we need to cache the audio on disk before playing it

        IN:
            audio_size - audio size

        RETURNS:
            True if we need to cache it before playing
            False otherwise
        """
        return True if audio_size > store.ytm_globals.AUDIO_SIZE_LIMIT else False

    def ytm_findCache(audio_id):
        """
        Looks for cache on disk

        IN:
            audio_id - audio id (since we use it as a name for cache)

        RETURNS:
            a filepath to the cache if we already have it (even if it's small)
            or False if found nothing
        """
        directory = store.ytm_globals.FULL_MUSIC_DIRECTORY + audio_id + store.ytm_globals.EXTENSION

        return directory if os.path.isfile(directory) else False

    def ytm_bytesToAudioData(_bytes, name="None"):
        """
        Converts stream of bytes into AudioData obj which can be played
        via renpy's audio system

        IN:
            _bytes - a stream of bytes we will convert
            name - a name to use for that object
                (Default: "None")

        RETURNS:
            an AudioData object
        """
        # NOTE: I could generate a name instead of using "None"
        return AudioData(_bytes, name)

    def ytm_cacheData_RAM(url, content_size):
        """
        Caches data in RAM to use it right away
        TODO: Can I merge both functions into 1? ¯\_(ツ)_/¯

        IN:
            url - a url for the data
            content_size - the data's size

        RETURNS:
            The cache if we successfully downloaded it, False if got an exception
        """
        cache = b""
        min_threshold = 0
        max_threshold = store.ytm_globals.REQUEST_CHUNK
        headers = {
            "User-Agent": "Just Monika! (MAS v. %s)" % config.version,
            "Range": "bytes=%s-%s" % (min_threshold, max_threshold)
        }

        try:
            # TODO: should have this part only once
            # Probably will require rewriting
            req = urllib2.Request(url=url, headers=headers)
            response = urllib2.urlopen(req)

            while True:
                cache_buffer = response.read(store.ytm_globals.WRITING_CHUNK)

                if not cache_buffer:
                    break

                cache += cache_buffer
                cache_size = len(cache)

                if (
                    cache_size == max_threshold
                    and not cache_size == content_size
                ):
                    min_threshold = max_threshold
                    max_threshold += store.ytm_globals.REQUEST_CHUNK
                    headers["Range"] = "bytes=%s-%s" % (min_threshold, max_threshold)
                    req = urllib2.Request(url=url, headers=headers)
                    response = urllib2.urlopen(req)

        except Exception as e:
            ytm_writeLog("Failed to cache audio data.", e)
            return False

        return cache

    def ytm_cacheData_Disk(url, content_size, directory):
        """
        Caches data on disk to use it later
        TODO: Can I merge both functions into 1? ¯\_(ツ)_/¯

        IN:
            url - a url for the data
            content_size - the data's size
            directory - a directory we are going to save the cache to
                NOTE: should include the file's name

        RETURNS:
            The cache if we successfully downloaded it, False if got an exception
        """
        cache_size = 0
        min_threshold = 0
        max_threshold = store.ytm_globals.REQUEST_CHUNK
        headers = {
            "User-Agent": "Just Monika! (MAS v. %s)" % config.version,
            "Range": "bytes=%s-%s" % (min_threshold, max_threshold)
        }

        try:
            req = urllib2.Request(url=url, headers=headers)
            response = urllib2.urlopen(req)

            with open(directory, 'wb') as audio_cache:
                while True:
                    cache_buffer = response.read(store.ytm_globals.WRITING_CHUNK)

                    if not cache_buffer:
                        break

                    cache_size += len(cache_buffer)
                    audio_cache.write(cache_buffer)

                    if (
                        cache_size == max_threshold
                        and not cache_size == content_size
                    ):
                        min_threshold = max_threshold
                        max_threshold += store.ytm_globals.REQUEST_CHUNK
                        headers["Range"] = "bytes=%s-%s" % (min_threshold, max_threshold)
                        req = urllib2.Request(url = url, headers=headers)
                        response = urllib2.urlopen(req)

        except Exception as e:
            ytm_writeLog("Failed to cache audio data.", e)
            return False

        return directory

    def ytm_cacheFromRAM(_bytes, directory):
        """
        Moves the cache from RAM to disk to use it later

        IN:
            _bytes - data we will write
            directory - a directory we are going to save the cache to
                NOTE: should include the file's name

        RETURNS:
            True if successful, False oethrwise
        """
        try:
            with open(directory, 'wb') as audio_cache:
                audio_cache.write(_bytes)
        except Exception as e:
            ytm_writeLog("Failed to write cache on disk from RAM.", e)
            return False

        return True

    def ytm_playAudio(audio, clear_queue=True, channel="music"):
        """
        Plays audio files/data

        IN:
            audio - an audio file (can be a list of files too)
            clear_queue - True clears the queue and play audio, False adds to the the end
                (Default: True)
            channel - a RenPy channel we will play the audio in
                (Default: "music")
        """
        if clear_queue:
            renpy.music.stop(channel, 2)
            store.songs.current_track = "YouTube Music"
            store.songs.selected_track = store.songs.FP_NO_SONG
            persistent.current_track = store.songs.FP_NO_SONG

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
            ytm_writeLog("Failed to play audio.", e)
            return False

        else:
            store.ytm_globals.is_playing = True
            return True

        finally:
            try:
                persistent._seen_audio.pop(audio)
            except:
                pass

        # TODO: take a look at
        # renpy.music.set_queue_empty_callback

# # # THREADING STUFF

init -5 python:
    import store.mas_threading as mas_threading

    def __ytm_th_Search(raw_search_request):
        """
        A func we use in threading to get search results

        IN:
            raw_search_request - raw user's search request

        RETURNS:
            videos data
        """
        return ytm_getSearchResults(ytm_requestHTML(ytm_toSearchURL(raw_search_request)))

    def __ytm_th_PlayAudio(url, video_id, audio_size, clear_queue):
        """
        Caches small audio and plays it in thread

        IN:
            url - a url to that audio
            video_id - the video's id
            audio_size - size of the audio
            clear_queue - should we clear the queue or not

        RETURNS:
            cache if we were able to successfully download it and play
            False if got an exception
        """
        cache = ytm_cacheData_RAM(url, audio_size)
        if cache and ytm_playAudio(ytm_bytesToAudioData(cache, video_id), clear_queue):
                return cache
        # got an exception somewhere
        return False

    def __ytm_th_GetAudioInfo(url):
        """
        Runs ytm_getAudioInfo() in thread for better performance

        IN:
            url - a url we will get data from

        RETURNS:
            a dict with various data (check ytm_getAudioInfo() for more info)
        """
        return ytm_getAudioInfo(url)

    def __ytm_th_CacheFromRAM(_bytes, directory):
        """
        Writes bytes from RAM on disk using threading

        IN:
            _bytes - data we will write
            directory - a directory we are going to save the cache to
                NOTE: should include the file's name

        RETURNS:
            True if successful otherwise False
        """
        return ytm_cacheFromRAM(_bytes, directory)

    def __ytm_th_CacheFromURL(url, content_size, directory):
        """
        Runs ytm_cacheData_Disk() in thread, after downloading the cache
        will push an event so [player] will know we're good

        IN:
            url - a url we will download from
            content_size - the data's size
            directory - a directory we are going to save the cache to
                NOTE: should include the file's name

        RETURNS:
            True if we successefully downloaded and queued,
            False if got an exception
        """
        cache = ytm_cacheData_Disk(url, content_size, directory)
        if cache:
            # NOTE: The Play function uses short paths so we need to cut a part of the path here
            store.ytm_globals.audio_to_queue = directory.split(renpy.config.gamedir.replace("\\", "/"), 1)[1]
            pushEvent("ytm_monika_finished_caching_audio")
            return True
        # got an exception somewhere
        return False

    def ytm_updateThreadArgs(thread, args):
        """
        Sets new args for the thread

        IN:
            thread - a thread we are changing args for
            args - a list of args
        """
        thread._th_args = args

    def ytm_resetThread(thread):
        """
        Resets thread properties so we can start another one
        regardless of if it's ready or not

        IN:
            thread - a thread we reset
        """
        thread._th_result = None
        thread._th_done = True
        thread.ready = True

    ytm_search_music = mas_threading.MASAsyncWrapper(__ytm_th_Search)
    ytm_get_audio_info = mas_threading.MASAsyncWrapper(__ytm_th_GetAudioInfo)
    ytm_play_audio = mas_threading.MASAsyncWrapper(__ytm_th_PlayAudio)
    ytm_cache_audio_from_ram = mas_threading.MASAsyncWrapper(__ytm_th_CacheFromRAM)
    ytm_cache_audio_from_url = mas_threading.MASAsyncWrapper(__ytm_th_CacheFromURL)