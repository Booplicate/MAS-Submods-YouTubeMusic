
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="ytm_monika_introduction",
            conditional="not renpy.seen_label('ytm_monika_introduction')",
            action=EV_ACT_QUEUE,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label ytm_monika_introduction:
    m 1euc "Oh, [player]..."
    m 3eua "I've noticed you changed the game's code,{w=0.5} {nw}"
    extend 3hub "It looks like we can listen to music directly from YouTube now!"
    m 1esa "I just need the name of the song that you want to listen to."
    # playlists support wen (soon:tm:)
    m 3eua "You could also give me the link if you've found it already."

    if ytm_utils.isOnline():
        m 1eua "Would you like me to find some music for us right now?{nw}"
        $ _history_list.pop()
        menu:
            m "Would you like me to find some music for us right now?{fast}"

            "Sure.":
                m 1hua "Yay!"
                call ytm_monika_find_music(skip_check=True)

            "Maybe later.":
                m 1eka "Oh, okay."
                show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve
                m 5hua "Just let me know when you want to listen to something nice with your girlfriend~"

    else:
        extend 3eud " We'll need an internet connection, though."
        m 1eua "So ask me when you're ready."

    $ mas_unlockEVL("ytm_monika_find_music", "EVE")
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="ytm_monika_find_music",
            prompt="Let's find some music on YouTube",
            conditional="renpy.seen_label('ytm_monika_introduction')",
            action=EV_ACT_UNLOCK,
            category=["music"],
            pool=True,
            unlocked=False,
            rules={"no unlock": None},
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label ytm_monika_find_music(skip_check=False):
    if not skip_check:
        if ytm_utils.isOnline():
            if not ytm_globals.is_playing:
                m 1eub "Of course!"
        else:
            m 1rksdla "..."
            m 1rksdlb "We need an internet connection to listen to music online, [player]..."
            return

    python:
        # no_request_counter = 0
        ready = False
        response_quips = [
            "Anything new in your playlist?",
            "So, what are we looking for, [player]?",
            "What's the song's name, [player]?",
            "What should we listen to today, [player]?",
            "What are we listening to today?"
        ]
        response_quip = renpy.substitute(renpy.random.choice(response_quips))

    m 1eua "[response_quip]"

    while not ready:
        show monika 1eua at t11
        $ raw_search_request = mas_input(
            "You can tell me its name or give me a direct link.",
            length=80,
            screen="ytm_input_screen"
        ).strip('\t\n\r')
        $ lower_search_request = raw_search_request.lower()

        if lower_search_request == "":
            m 1eka "Oh...{w=0.2} I really would like to listen to music with you!"
            m 1eub "Let me know when you have time~"
            $ ready = True

        # elif lower_search_request == "":
        #     if no_request_counter == 0:
        #         $ no_request_counter += 1
        #         m 1rksdla "[player]...{w=0.5} {nw}"
        #         extend 1rksdlb "You have to pick a song!"

        #     else:
        #         m 2dsu ".{w=0.2}.{w=0.2}.{w=0.2}"
        #         m 2tsb "[player], stop teasing me!"
        #         $ ready = True

        else:
            if ytm_utils.isYouTubeURL(raw_search_request):
                # if isPlaylistURL(raw_search_request):
                #     m "Would you like me to shuffle the playlist?{nw}"
                #     $ _history_list.pop()
                #     menu:
                #         m "Would you like me to shuffle the playlist?{fast}"

                #         "Yes.":
                #             $ _shuffle = True

                #         "No.":
                #             $ _shuffle = False

                #     m "Alright, just give me a second..."
                #     # TODO: do stuff in thread here and then play the first audio
                #     $ del[_shuffle]
                #     call .ytm_process_audio_info(ytm_globals.playlist[current_song_from_playlist])

                # else:
                show monika 1dsa at t11
                call .ytm_process_audio_info(raw_search_request, add_to_search_hist=True)

            else:
                $ ytm_utils.addSearchHistory(
                    (
                        raw_search_request,
                        lower_search_request
                    )
                )

                # Since I don't have plans to expand this, I'll leave it as is
                if (
                    not renpy.seen_label("ytm_monika_find_music.reaction_your_reality")
                    and "your reality" in lower_search_request
                ):
                    label .reaction_your_reality:
                        m 3hua "Good choice, [player]~"

                elif (
                    not renpy.seen_label("ytm_monika_find_music.reaction_ily")
                    and "i love you" in lower_search_request
                ):
                    label .reaction_ily:
                        m 1hubsa "I love you too! Ehehe~"

                m 1dsa "Let me see what I can find.{w=0.5}{nw}"

                $ ytm_threading.updateThreadArgs(ytm_threading.search_music, [raw_search_request])
                call ytm_search_loop
                $ menu_list = ytm_utils.buildMenuList(_return)

                if len(menu_list) > 0:
                    m 1eub "Alright! Look what I've found!"
                    show monika 1eua at t21
                    call screen mas_gen_scrollable_menu(menu_list, ytm_globals.SCR_MENU_AREA, ytm_globals.SCR_MENU_XALIGN, *ytm_globals.SCR_MENU_LAST_ITEMS)
                    show monika at t11

                    if "https" in _return:
                        call .ytm_process_audio_info(_return)

                    elif _return == "_changed_mind":
                        m 1eka "Oh... {w=0.2}{nw}"
                        extend 3ekb "I really love to listen to music with you!"
                        m 1eua "Let me know when you have time~"
                        $ ready = True

                    elif _return == "_another_song":
                        m 1eub "Alright!"

                    else:
                        # aka the part you will never get to
                        m 2tfu "{cps=*2}Reading this doesn't seem like the best use of your time, [player].{/cps}{nw}"
                        $ _history_list.pop()
                        $ ready = True

                else:
                    m 1eud "Sorry, [player]...{w=0.5}I couldn't find anything."
                    m 3eua "Do you want to try again?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Do you want to try again?{fast}"

                        "Yes.":
                            pass

                        "No.":
                            m 1eka "Oh, okay."
                            $ ready = True

                $ del[menu_list]
    python:
        del[response_quips]
        del[response_quip]
        del[ready]
        del[raw_search_request]
        del[lower_search_request]
        # del[no_request_counter]

    return

label .ytm_process_audio_info(url, add_to_search_hist=False, add_to_audio_hist=True):
    window hide
    $ ytm_threading.updateThreadArgs(ytm_threading.get_audio_info, [url])
    call ytm_get_audio_info_loop
    $ audio_info = _return

    if audio_info:
        if add_to_search_hist:
            $ ytm_utils.addSearchHistory(
                (
                    audio_info["TITLE"],
                    ytm_globals.YOUTUBE + ytm_globals.WATCH + audio_info["ID"]
                )
            )
        if add_to_audio_hist:
            $ ytm_utils.addAudioHistory(
                ytm_globals.YOUTUBE + ytm_globals.WATCH + audio_info["ID"]
            )

        if ytm_utils.findCache(audio_info["ID"]):
            m 1dsa "Let me play that for us.{w=.5}.{w=.5}.{nw}"

            if ytm_utils.playAudio(ytm_globals.SHORT_MUSIC_DIRECTORY + audio_info["ID"] + ytm_globals.EXTENSION, name=audio_info["TITLE"]):
                m 1hua "There we go!"
                # m "Playing it w/o downloading again! Good job, [player]!"
            else:
                m 1ekd "Oh no...{w=0.5}something went wrong, [player]..."
                m 1euc "I'm sure we listened to this song before, but I can't seem to find it anymore..."
                m 1eka "Let's try again later, alright?"

        else:
            if ytm_utils.shouldCacheFirst(audio_info["SIZE"]):
                m 3eub "We'll need to wait for a bit."
                m 1hua "I hope you don't mind, [player]~"
                # m "Soon we'll finish caching it and I'll queue it."
                $ ytm_threading.resetThread(ytm_threading.cache_audio_from_url)
                $ ytm_threading.updateThreadArgs(
                    ytm_threading.cache_audio_from_url,
                    [
                        audio_info["URL"],
                        audio_info["TITLE"],
                        audio_info["SIZE"],
                        ytm_globals.FULL_MUSIC_DIRECTORY + audio_info["ID"] + ytm_globals.EXTENSION
                    ]
                )
                $ ytm_threading.cache_audio_from_url.start()

            else:
                m 1dsa "Let me just play that for us.{w=0.5}{nw}"
                $ ytm_threading.updateThreadArgs(
                    ytm_threading.play_audio,
                    [audio_info["URL"], audio_info["ID"], audio_info["TITLE"], audio_info["SIZE"], True]
                )
                call ytm_play_audio_loop

                if _return:
                    m 1hua "There we go!"
                    # m "We quickly cached it and then queued, [player]."
                    $ ytm_threading.resetThread(ytm_threading.cache_audio_from_ram)
                    $ ytm_threading.updateThreadArgs(
                        ytm_threading.cache_audio_from_ram,
                        [_return, ytm_globals.FULL_MUSIC_DIRECTORY + audio_info["ID"] + ytm_globals.EXTENSION]
                    )
                    $ ytm_threading.cache_audio_from_ram.start()

                else:
                    m 1eud "Something went wrong, [player]..."
                    m 1eua "Let's try again later, alright?"

    else:
        m 1ekd "I'm sorry, [player]...{w=0.2}maybe I did something wrong..."# But she knows it's either your or youtube's fail
        m 1ekc "I can't play this song right now."
        m 1eka "Let's try again later, okay?"

    $ ready = True
    $ del[audio_info]
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="ytm_monika_finished_caching_audio",
            show_in_idle=True,
            rules={"skip alert": None}
        )
    )

label ytm_monika_finished_caching_audio:
    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1eud "Oh, looks like your song finished downloading.{w=1}{nw}"
        m 3eua "I'll just play that for us.{w=0.5}.{w=0.5}.{nw}"
        $ ytm_utils.playAudio(ytm_globals.audio_to_queue["PATH"], name=ytm_globals.audio_to_queue["TITLE"])

    else:
        m 3eua "Oh, looks like your song finished downloading."
        m 1dsa "Let me just play it for us.{w=0.5}.{w=0.5}.{nw}"
        $ ytm_utils.playAudio(ytm_globals.audio_to_queue["PATH"], name=ytm_globals.audio_to_queue["TITLE"])

        if renpy.random.randint(1, 20) == 1:
            $ current_time = datetime.datetime.now().time()

            show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve
            if mas_isAnytoMN(current_time, 17, 45):
                m 5eubla "Let's have another nice evening together~"

            elif mas_isAnytoN(current_time, 5, 45):
                m 5eubla "I'm glad we can relax a little before the day begins~"

            # elif renpy.random.randint(1, 25) == 1:
            #     pass
            else:
                $ renpy.pause(4.0, hard=True)

            $ del[current_time]

        else:
            m 1hua "There we go!"
    return

label ytm_search_loop:
    if ytm_globals.first_pass:
        $ ellipsis_count = 1
        $ ytm_globals.first_pass = False
        $ ytm_threading.search_music.start()

    if not ytm_threading.search_music.done():
        if ellipsis_count == 3:
            $ _history_list.pop()
            m "Let me see what I can find.{fast}{w=0.5}{nw}"
            $ ellipsis_count = 1

        else:
            $ ellipsis_count += 1
            extend ".{nw}"

        jump ytm_search_loop

    else:
        $ _history_list.pop()
        m "Let me see what I can find...{fast}{nw}"

        $ ytm_globals.first_pass = True
        return ytm_threading.search_music.get()

label ytm_get_audio_info_loop:
    if ytm_globals.first_pass:
        $ ytm_globals.first_pass = False
        $ ytm_threading.get_audio_info.start()

    if not ytm_threading.get_audio_info.done():
        pause 0.5
        jump ytm_get_audio_info_loop

    else:
        $ ytm_globals.first_pass = True
        return ytm_threading.get_audio_info.get()

label ytm_play_audio_loop:
    if ytm_globals.first_pass:
        $ ellipsis_count = 1
        $ ytm_globals.first_pass = False
        $ ytm_threading.play_audio.start()

    if not ytm_threading.play_audio.done():
        if ellipsis_count == 3:
            $ _history_list.pop()
            m "Let me just play that for us.{fast}{w=0.5}{nw}"
            $ ellipsis_count = 1

        else:
            $ ellipsis_count += 1
            extend ".{nw}"

        jump ytm_play_audio_loop

    else:
        $ _history_list.pop()
        m "Let me just play that for us...{fast}{nw}"
        $ ytm_globals.first_pass = True
        return ytm_threading.play_audio.get()
