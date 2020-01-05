
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel = "ytm_monika_introduction",
            conditional = "not renpy.seen_label('ytm_monika_introduction')",
            action = EV_ACT_QUEUE,
            aff_range = (mas_aff.NORMAL, None)
        )
    )

label ytm_monika_introduction:
    m 1lua "[player]..."
    m 1eua "I've noticed you changed the game's code."
    m 1eub "Looks like we can listen to your music directly from YouTube!"
    m 3eub "I just need the name of the song that you want to listen to."
    # playlists support wen
    m 1eua "Or you could give me the link if you've found it already."
    if ytm_isOnline():
        m "Do you want me to find some music for us right now?{nw}"
        $ _history_list.pop()
        menu:
            m "Do you want me to find some music for us right now?{fast}"

            "Sure.":
                m 1hua "Yay!"
                call ytm_monika_find_music(skip_check = True)

            "Maybe later.":
                m 1eua "Oh, okay."
                show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve
                m 5hua "Let me know when you want to listen to something nice with your girlfriend~"
    else:
        m 3eud "We need an internet connection, though."
        m 1eua "So ask me when you're ready."

    $ mas_unlockEVL("ytm_monika_find_music", "EVE")
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel = "ytm_monika_find_music",
            prompt = "Let's find some music on YouTube",
            conditional = "renpy.seen_label('ytm_monika_introduction')",
            action = EV_ACT_UNLOCK,
            category = ["music"],
            pool = True,
            unlocked = False,
            rules = {"no unlock": None},
            aff_range = (mas_aff.NORMAL, None)
        )
    )

label ytm_monika_find_music(skip_check = False):
    if not skip_check:
        if ytm_isOnline():
            m 1eub "Of course!"
        else:
            m 1rksdla "..."
            m 1ekb "We need an internet connection to listen to music online, [player]."
            return
    python:
        no_request_counter = 0
        ready = False
        response_quips = [
            "Anything new in your playlist?",
            "So, what are we looking for, [player]?",
            "Tell me the song's name, [player].",
            "Which song will we listen to today?"
        ]
        response_quip = renpy.substitute(renpy.random.choice(response_quips))
    m 1eua "[response_quip]"
    $ del[response_quips]
    $ del[response_quip]
    while not ready:
        show monika 1eua at t11
        $ raw_search_request = renpy.input("Type 'Nevermind' if you change your mind.", length = 80).strip('\t\n\r')
        $ lower_search_request = raw_search_request.lower()
        if lower_search_request == "nevermind":
            m 1eka "Oh...{w=.2} I really would like to listen to music with you!"
            m 1eub "Let me know when you have time~"
            $ ready = True
        elif lower_search_request == "":
            if no_request_counter == 0:
                $ no_request_counter += 1
                m 1dsc "[player]..."
                m 1esc "Do you want me to find a song or no?"
            else:
                m 2dfu "{i}*sigh*{/i}"
                m 2efb "Stop teasing me, [player]!"
                $ ready = True
        else:
            if ytm_isYouTubeURL(raw_search_request):
                show monika 1dsa at t11
                call .ytm_process_audio_info(raw_search_request)
            else:
                m 1dsa "Give me some time.{nw}"
                $ ytm_updateThreadArgs(ytm_search_music, [raw_search_request])
                call ytm_search_loop
                $ menu_list = ytm_buildMenuList(_return)
                if len(menu_list) > 2:
                    m 1eub "Alright! Look what I've found!"
                    show monika 1eua at t21
                    call screen mas_gen_scrollable_menu(menu_list, (835, 40, 440, 640), -0.05)
                    show monika at t11
                    if "https" in _return:
                        call .ytm_process_audio_info(_return)
                    elif _return == "_changed_mind":
                        m 1eka "Oh... {w=.2}{nw}"
                        extend 3ekb "I really love to listen to music with you!"
                        m 1eua "Let me know when you have time~"
                        $ ready = True
                    elif _return == "_another_song":
                        m 1eub "Alright!"
                    else:
                        # aka the part you will never get to
                        m 2tfu "Reading this doesn't seem like the best use of your time, [player]."
                        $ ready = True
                else:
                    m 1eud "I couldn't find anything, [player]."
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
        del[ready]
        del[raw_search_request]
        del[lower_search_request]
    return

label .ytm_process_audio_info(url):
    window hide
    $ ytm_updateThreadArgs(ytm_get_audio_info, [url])
    call ytm_get_audio_info_loop
    $ audio_info = _return
    if audio_info:
        if ytm_findCache(audio_info["ID"]):
            m 1dsa "Let me tune it up.{w=.5}.{w=.5}.{nw}"
            if ytm_playAudio(store.ytm_globals.SHORT_MUSIC_DIRECTORY + audio_info["ID"] + store.ytm_globals.EXTENSION):
                m 1hua "There we go!"
                # m "Playing it w/o downloading again! Good job, [player]!"
            else:
                m 1eud "Something went wrong, [player]..."
                m 1euc "I'm sure we listened to this song before, but I can't find it..."
                m 1eua "Let's try again later."
        else:
            if ytm_shouldCacheFirst(audio_info["SIZE"]):
                m 3eub "We need to wait for a bit."
                m 1hua "I hope you don't mind~"
                # m "Soon we'll finish caching it and I'll queue it."
                $ ytm_updateThreadArgs(ytm_cache_audio_from_url, [audio_info["URL"], audio_info["SIZE"], store.ytm_globals.FULL_MUSIC_DIRECTORY + audio_info["ID"] + store.ytm_globals.EXTENSION])
                $ ytm_cache_audio_from_url.start()
            else:
                m 1dsa "Let me tune it up.{nw}"
                $ ytm_updateThreadArgs(ytm_play_audio, [audio_info["URL"], audio_info["ID"], audio_info["SIZE"], True])
                call ytm_play_audio_loop
                if _return:
                    m 1hua "There we go!"
                    # m "We quickly cached it and then queued, [player]."
                    $ ytm_updateThreadArgs(ytm_cache_audio_from_ram, [_return, store.ytm_globals.FULL_MUSIC_DIRECTORY + audio_info["ID"] + store.ytm_globals.EXTENSION])
                    $ ytm_cache_audio_from_ram.start()
                else:
                    m 1eud "Something went wrong, [player]..."
                    m 1eua "Let's try again later."
    else:
        m 1rkd "I'm sorry, [player]...{w=.2} Maybe I did something wrong."# But she knows it's either your or youtube's fail
        m 1ekc "I can't play this song right now."
        m 1eka "Let's try again later."
    $ ready = True
    $ del[audio_info]
    return

init 5 python:
    addEvent(Event(persistent.event_database, eventlabel = "ytm_monika_finished_caching_audio", show_in_idle = True, rules = {"skip alert": None}))

label ytm_monika_finished_caching_audio:
    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 3eua "Oh, looks like we can listen to that song now.{w=2}{nw}"
        $ ytm_playAudio(store.ytm_globals.audio_to_queue)
    else:
        m 3eua "Oh, looks like we can listen to that song now."
        m 1dsa "Let me just put it on for us.{w=.5}.{w=.5}.{nw}"
        # TODO: maybe she could ask you if you want to play it right away or actually queue it?
        $ ytm_playAudio(store.ytm_globals.audio_to_queue)
        if renpy.random.randint(1, 25) == 1:
            $ current_time = datetime.datetime.now().time()
            show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve
            if mas_isAnytoMN(current_time, 17, 45):
                m 5eubla "Let's have another nice and relaxing evening together~"
            elif mas_isAnytoN(current_time, 5, 45):
                m 5eubla "I'm glad we can relax a little before you will be busy~"
            # elif renpy.random.randint(1, 25) == 1:
            #     pass
            else:
                pause 3.0
            $ del[current_time]
        else:
            m 1hua "There we go!"
    return

label ytm_search_loop:
    if store.ytm_globals.first_pass:
        $ store.ytm_globals.first_pass = False
        $ ytm_search_music.start()
    if not ytm_search_music.done():
        $ _history_list.pop()
        m "Give me some time..{fast}{nw}"
        jump ytm_search_loop
    else:
        $ _history_list.pop()
        m "Give me some time...{fast}{nw}"
        $ store.ytm_globals.first_pass = True
        return ytm_search_music.get()

label ytm_get_audio_info_loop:
    if store.ytm_globals.first_pass:
        $ store.ytm_globals.first_pass = False
        $ ytm_get_audio_info.start()
    if not ytm_get_audio_info.done():
        jump ytm_get_audio_info_loop
    else:
        $ store.ytm_globals.first_pass = True
        return ytm_get_audio_info.get()

label ytm_play_audio_loop:
    if store.ytm_globals.first_pass:
        $ store.ytm_globals.first_pass = False
        $ ytm_play_audio.start()
    if not ytm_play_audio.done():
        $ _history_list.pop()
        m "Let me tune it up..{fast}{nw}"
        jump ytm_play_audio_loop
    else:
        $ _history_list.pop()
        m "Let me tune it up...{fast}{nw}"
        $ store.ytm_globals.first_pass = True
        return ytm_play_audio.get()
