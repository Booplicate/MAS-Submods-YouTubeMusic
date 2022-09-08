
# # # Startup checks

init 50 python:
    import os

    # Make the folders if needed
    if not os.path.isdir(ytm_globals.FULL_YT_SIG_DIRECTORY):
        try:
            os.makedirs(ytm_globals.FULL_YT_SIG_DIRECTORY)
        except Exception as e:
            # There's nothing that would create the folder now,
            # which means it has to be a perm issue
            store.ytm_utils.report_error("Failed to create cache directory", e)

    if not os.path.isdir(ytm_globals.FULL_YT_NSIG_DIRECTORY):
        try:
            os.makedirs(ytm_globals.FULL_YT_NSIG_DIRECTORY)

        except Exception as e:
            # There's nothing that would create the folder now,
            # which means it has to be a perm issue
            store.ytm_utils.report_error("Failed to create cache directory", e)

    # Check connection on startup
    ytm_utils.is_online()

# # # "GLOBALS" STUFF

init -20 python in ytm_globals:
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
    SCR_MENU_ANOTHER_SING = "_another_song"
    SCR_MENU_CHANGED_MIND = "_changed_mind"
    # (prompt, return, italics, bold, offset)
    SCR_MENU_LAST_ITEMS = (
        ("I want to find another song.", SCR_MENU_ANOTHER_SING, False, False, 20),
        ("I changed my mind.", SCR_MENU_CHANGED_MIND, False, False, 0),
    )

    # Maximum audio size to play from RAM (bytes)
    AUDIO_SIZE_LIMIT = 10 * 1048576

    # Url parts
    GOOGLE = "http://www.google.com/"
    YOUTUBE = "https://www.youtube.com/"
    SEARCH = "results?search_query="
    WATCH = "watch?v="

    HEADERS = {
        # Mozilla/5.0 (Windows NT 6.1; Win64; x64)
        "User-Agent": "Just Monika! (Monika After Story v{0})".format(renpy.config.version),
        "Accept-Language": "en-US",
        "Content-Language": "en-US",
        "Accept-Charset": "utf8"
    }

    TIMEOUT = 10

    # We keep cache here
    GAME_DIR = renpy.config.gamedir.replace("\\", "/")
    SHORT_MUSIC_DIRECTORY = "/Submods/YouTube Music/temp/"
    FULL_MUSIC_DIRECTORY = GAME_DIR + SHORT_MUSIC_DIRECTORY
    FULL_YT_SIG_DIRECTORY = FULL_MUSIC_DIRECTORY + "/youtube-sigfuncs/"
    FULL_YT_NSIG_DIRECTORY = FULL_MUSIC_DIRECTORY + "/youtube-nsig/"
    # Cache extension
    EXTENSION = ".cache"

    # Params for yt-dl
    # NOTE: these might be interesting:
    #   prefer_insecure
    YDL_FORMAT_AUDIO_OPUS = "bestaudio[acodec=opus]"
    YDL_FILENAME_FORMAT = f"%(id)s{EXTENSION}"
    YDL_OPTS = {
        # Redirect the cache to our folder (youtube-sigfuncs will be created automatically)
        "cachedir": FULL_MUSIC_DIRECTORY,
        # RenPy has broken stdio, we better not to use it
        "quiet": True,
        # Don't report progress either
        "noprogress": True,
        # NOTE: This probably doesn't work, but won't do harm either
        "user_agent": HEADERS["User-Agent"],
        # I hate this, but it's the only way to fix certifs
        # I wish ytdl used requests...
        "nocheckcertificate": True,
        "mark_watched": False,
        # No yt-dl extra requests
        "call_home": False,
        # Output file format
        "outtmpl": f"{FULL_MUSIC_DIRECTORY}{YDL_FILENAME_FORMAT}",
        # We need just audio in opus
        "format": YDL_FORMAT_AUDIO_OPUS,
        # "verbose": True,
    }

    # Loop counter
    loop_count = 0
    # a dict with the title and path to the audio we need to queue
    audio_to_queue = {"title": "", "path": ""}
    # Do we play an audio or no
    is_playing = False
    # all videos URLs from the playlist we're currently listening to
    # playlist = []
    # id of the current track from the playlist
    # current_song_from_playlist = 0
    # a dict of search requests, values are urls/queries
    search_history = dict()
    # a dict of played audio (youtube ids), values unused
    audio_history = dict()

init -20 python in ytm_screen_utils:
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

init -15 python in ytm_utils:
    import os
    import io
    import unicodedata
    from time import time
    from threading import Thread
    from collections import namedtuple

    import requests
    import youtube_dl

    import store
    from store import ytm_globals
    from store.mas_submod_utils import submod_log

    youtube_dl.std_headers["User-Agent"] = ytm_globals.YDL_OPTS["user_agent"]


    VideoInfo = namedtuple(
        "VideoInfo",
        ("title", "url", "id")
    )

    AudioInfo = namedtuple(
        "AudioInfo",
        ("title", "url", "id", "stream_url", "size")
    )


# # # UTIL STUFF

    def _format_log(msg: str, err: Exception|None) -> str:
        if e is not None:
            e = f": {e}"

        else:
            e = ""

        return f"[YTM]: {msg}{e}"

    def report_error(msg: str, err: Exception|None = None, print_stack: bool = False):
        submod_log.error(_format_log(msg, err), exc_info=print_stack)

    def report_ingo(msg: str, print_stack: bool = False):
        submod_log.info(_format_log(msg, None), exc_info=print_stack)

    def delete_files(path, extension, e_str=None):
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
            report_error(e_str, e)

    def delete_cache():
        """
        Deletes the cache
        """
        renpy.music.stop("music", 0)

        delete_files(
            ytm_globals.FULL_MUSIC_DIRECTORY,
            ytm_globals.EXTENSION,
            "Couldn't remove cache."
        )

    def delete_signatures():
        """
        Deletes youtube signatures
        """
        delete_files(
            ytm_globals.FULL_YT_SIG_DIRECTORY,
            ".json",
            "Couldn't remove signatures."
        )
        delete_files(
            ytm_globals.FULL_YT_NSIG_DIRECTORY,
            ".json",
            "Couldn't remove signatures."
        )

    def cleanup():
        """
        Makes it so you can't call my submod a bloatware
        """
        delete_cache()
        delete_signatures()

    def add_search_history(search_request, value):
        """
        Adds the given entry to the search history

        IN:
            search_request - string with the search query
            value - returned value for the query (either a video url, or the query itself)
        """
        if search_request in ytm_globals.search_history:
            del ytm_globals.search_history[search_request]

        ytm_globals.search_history[search_request] = value

    def add_audio_history(url):
        """
        Adds the given entry to the audio history

        IN:
            url - full url to the audio
        """
        if url in ytm_globals.audio_history:
            del ytm_globals.audio_history[url]

        ytm_globals.audio_history[url] = None

    def is_online(force_update=False):
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
                requests.get(
                    ytm_globals.GOOGLE,
                    headers=ytm_globals.HEADERS,
                    timeout=ytm_globals.TIMEOUT
                )
                ytm_globals.has_connection = True

            except Exception as e:
                # Extra handling for the Too Many Requests response
                if hasattr(e, "response") and e.response and response.status_code == 429:
                    ytm_globals.has_connection = True

                else:
                    report_error("No connection", e)
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
        if not string:
            return ""

        string = (unicodedata.normalize("NFKD", string)
            .encode("ascii", "ignore")
            .decode())

        # Workaround if we get a title longer than 100 chars (somehow?)
        if len(string) > 100:
            string = string[:95] + "(...)"
        # Clean the string
        string = string.strip().replace("[", "[[").replace("{", "{{")

        return string

# # # URL STUFF

    def is_youtube_url(string):
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

# # # VIDEO STUFF

    def get_search_results(search_request: str):
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
                report_error("Failed to retrieve search results", e, True)
                return videos_info

            # This probably cannot be None nor even empty, but just in case
            if not yt_dl_info:
                report_error("Got invalid data from yt-dl: '{}'".format(yt_dl_info))
                return videos_info

            # NOTE: This may contain a generator
            entries = yt_dl_info.get("entries", ())
            total_songs = 0
            for entry in entries:
                title = clean_string(entry.get("title", "[An untitled video]"))
                uploader = clean_string(entry.get("uploader", "[Unknown author]"))
                id_ = entry.get("id", entry.get("url", None))

                # If we couldn't get the id, we should skip this video
                if id_ is None or len(id_) != 11:
                    report_error(f"Got invalid video id: '{id_}'")
                    continue

                url = ytm_globals.YOUTUBE + ytm_globals.WATCH + id_

                videos_info.append(
                    VideoInfo(
                        title + " - " + uploader,
                        url,
                        id_
                    )
                )
                total_songs += 1
                if total_songs >= ytm_globals.SEARCH_LIMIT:
                    return videos_info

        return videos_info

    def build_menu_data(videos_info):
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
                video_info.title,
                video_info,
                (video_info.url not in ytm_globals.audio_history),
                False
            )
            for video_info in videos_info
        ]

# # # AUDIO STUFF

    def get_audio_info(url: str) -> AudioInfo|None:
        """
        Request the video's audio data

        IN:
            url - video's URL

        OUT:
            AudioInfo or None
        """
        tries = ytm_globals.STREAM_REQUEST_ATTEMPTS
        seen_errors = set()
        while tries > 0:
            tries -= 1
            try:
                with youtube_dl.YoutubeDL(dict(ytm_globals.YDL_OPTS)) as yt_dl:
                    yt_dl_info = yt_dl.extract_info(url, download=False)

                    # Get list of dicts
                    formats = yt_dl_info.get("formats", ())
                    if not formats:
                        report_error("Got empty audio data from yt-dl")
                        return None

                    # Now filter so we get the best format that works in renpy
                    best_format = max(formats, key=lambda frm: (frm.get("acodec") == "opus", frm.get("abr"), frm.get("asr")))
                    if best_format.get("acodec") != "opus":
                        report_error("No audio streams with opus codec found")
                        return None

                    title = clean_string(yt_dl_info.get("title", "[An untitled video]"))
                    uploader = clean_string(yt_dl_info.get("uploader", "[Unknown author]"))

                    id_ = yt_dl_info.get("id", yt_dl_info.get("url", None))
                    if id_ is None or len(id_) != 11:
                        report_error("Got invalid video id from yt-dl: '{}'".format(id_))
                        return None

                    content_size = None
                    stream_url = best_format.get("url")
                    if not stream_url:
                        if stream_url is None:
                            report_error("Audio stream is NoneType. Live streams are not supported yet")

                        else:
                            report_error("Got invalid stream url from yt-dl: '{}'".format(stream_url))
                        return None

                    content_size = best_format.get("filesize")
                    # Fallback if we got the wrong stream, or yt-dl couldn't return the CS
                    if not content_size:
                        try:
                            response = requests.head(
                                stream_url,
                                headers=ytm_globals.HEADERS,
                                timeout=ytm_globals.TIMEOUT
                            )
                            content_size = int(response.headers["Content-Length"])

                        except Exception as e:
                            report_error("Failed to request content size", e)
                            return None

            except Exception as e:
                e_type = type(e)
                if e_type not in seen_errors:
                    seen_errors.add(e_type)
                    report_error("Failed to get audio info", e, True)

                if tries <= 0:
                    return None

            else:
                # If we got the stream w/o exceptions, break the loop
                break

        return AudioInfo(
            title + " - " + uploader,
            url,
            id_,
            stream_url,
            content_size
        )

    def should_cache_first(audio_size: int) -> bool:
        """
        Decides if we need to cache the audio on disk before playing it

        IN:
            audio_size - audio size

        RETURNS:
            True if we need to cache it before playing
            False otherwise
        """
        return audio_size > ytm_globals.AUDIO_SIZE_LIMIT

    def does_cache_exist(audio_id: str) -> bool:
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

    def download_audio(url: str) -> bool:
        """
        Caches music from the url

        IN:
            url - a url to the data

        OUT:
            boolean
        """
        try:
            with youtube_dl.YoutubeDL(dict(ytm_globals.YDL_OPTS)) as yt_dl:
                yt_dl.extract_info(url, download=True)

        except Exception as e:
            report_error("Failed to cache audio data", e, True)
            return False

        return True

    def play_audio(
        audio,
        name=None,
        loop=True,
        clear_queue=True,
        fadein=2,
        set_ytm_flag=True
    ) -> bool:
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
            report_error("Failed to play audio", e, True)
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
            and is_online()
        ):
            spook_thread = Thread(target=_do_o31_spook)
            spook_thread.daemon = True
            spook_thread.start()

    def _do_o31_spook():
        """
        This mean function spooks you and takes all your candies
        """
        # start_ts = time()
        # # Credits to T.L.B. Orchestration
        # audio_info = get_audio_info("https://youtu.be/J7XtCHxVUto")
        # if audio_info:
        #     cache = cacheDataToRAM(audio_info["url"], audio_info["size"])
        #     end_ts = time()
        #     d_t = end_ts - start_ts
        #     if cache and d_t < 15:
        #         play_audio(
        #             bytesToAudioData(cache, "Spook~"),
        #             name="Spook~",
        #             loop=False,
        #             fadein=10,
        #             set_ytm_flag=False
        #         )

# # # THREADING STUFF

init -10 python in ytm_threading:
    import store
    from store import (
        ytm_globals,
        ytm_utils,
        mas_threading
    )
    # TODO: wrap all _th funcs in a try/except

    def _search_music_th(raw_search_request: str):
        """
        A func we use in threading to get search results and format them to display in the menu

        IN:
            raw_search_request - the user's search request

        RETURNS:
            videos data formatted for the menu
        """
        try:
            return ytm_utils.build_menu_data(
                ytm_utils.get_search_results(
                    raw_search_request
                )
            )

        except Exception as e:
            ytm_utils.report_error("_search_music_th failed", e)
            return None

    def _download_and_play_th(url, video_id, video_title, audio_size, clear_queue) -> bool:
        """
        Caches audio and plays it in a thread

        IN:
            url - a url to that audio
            video_id - the video's id
            video_title - the video's title
            audio_size - size of the audio
            clear_queue - should we clear the queue or not

        OUT:
            boolean
        """
        try:
            if ytm_utils.download_audio(url):
                audio = f"{ytm_globals.SHORT_MUSIC_DIRECTORY}{video_id}{ytm_globals.EXTENSION}"
                return ytm_utils.play_audio(audio, name=video_title, clear_queue=clear_queue)

        except Exception as e:
            ytm_utils.report_error("_download_and_play_th failed", e)

        return False

    def _get_audio_info_th(url):
        """
        Runs get_audio_info() in thread for better performance

        IN:
            url - the url we will get data from

        RETURNS:
            dict with various data (check get_audio_info() for more info)
        """
        try:
            return ytm_utils.get_audio_info(url)

        except Exception as e:
            ytm_utils.report_error("_get_audio_info_th failed", e)
            return None

    def _download_and_notify_th(url, title, content_size, directory) -> bool:
        """
        Caches audio in a thread, then pushes the notify event

        IN:
            url - a url we will download from
            title - the video's title
            content_size - the data's size
            directory - the directory we are going to save the cache to
                NOTE: should include the file's name

        OUT:
            boolean
        """
        try:
            if ytm_utils.download_audio(url):
                ytm_globals.audio_to_queue["title"] = title
                # NOTE: The play function uses short paths so we need to cut a part of the path here
                ytm_globals.audio_to_queue["path"] = directory.split(ytm_globals.GAME_DIR, 1)[1]
                store.pushEvent("ytm_monika_finished_caching_audio")
                return True

        except Exception as e:
            ytm_utils.report_error("_download_and_notify_th failed", e)

        return False

    def update_thread_args(thread, args):
        """
        Sets new args for the thread

        IN:
            thread - a thread we are changing args for
            args - a list of args
        """
        thread._th_args = args

    def reset_thread(thread):
        """
        Resets thread properties so we can start another one
        regardless of if it's ready or not

        IN:
            thread - the thread we reset
        """
        thread._th_result = None
        thread._th_done = True
        thread.ready = True

    search_music = mas_threading.MASAsyncWrapper(_search_music_th)
    get_audio_info = mas_threading.MASAsyncWrapper(_get_audio_info_th)
    download_and_play = mas_threading.MASAsyncWrapper(_download_and_play_th)
    download_and_notify = mas_threading.MASAsyncWrapper(_download_and_notify_th)
