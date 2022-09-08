
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

    if ytm_utils.is_online():
        m 1eua "Would you like me to find some music for us right now?{nw}"
        $ _history_list.pop()
        menu:
            m "Would you like me to find some music for us right now?{fast}"

            "Sure.":
                m 1hua "Yay!"
                call ytm_monika_find_music

            "Maybe later.":
                m 1eka "Oh, okay."
                show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5hua "Just let me know when you want to listen to something nice with your girlfriend~"

    else:
        extend 3eud " We'll need an internet connection, though."
        m 1eua "So ask me when you're ready."

    $ mas_unlockEVL("ytm_monika_find_music", "EVE")
    return "no_unlock"


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
            rules={"no_unlock": None, "bookmark_rule": store.mas_bookmarks_derand.WHITELIST},
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label ytm_monika_find_music:
    if ytm_utils.is_online():
        if not ytm_globals.is_playing:
            m 1eub "Of course!"
    else:
        m 1rksdla "..."
        m 1rksdlb "We need an internet connection to listen to music online, [player]..."
        return

    python:
        ready = False
        response_quips = [
            "Anything new in your playlist?",
            "So, what are we looking for, [mas_get_player_nickname()]?",
            "What's the song's name, [mas_get_player_nickname()]?",
            "What should we listen to today, [mas_get_player_nickname()]?",
            "What are we listening to today?"
        ]
        response_quip = renpy.substitute(renpy.random.choice(response_quips))

    m 1eua "[response_quip]"

    label .input_loop:
        show monika 1eua at t11
        $ raw_search_request = mas_input(
            "[response_quip]",
            length=80,
            screen="ytm_input_screen"
        ).strip('\t\n\r')
        $ lower_search_request = raw_search_request.lower()

        if lower_search_request == "":
            if not ytm_globals.is_playing or renpy.music.get_pause():
                m 1eka "Oh...{w=0.2}I really would like to listen to music with you!"
                m 1eub "Let me know when you have time~"

            else:
                m 1eka "Oh, okay."

        else:
            if ytm_utils.is_youtube_url(raw_search_request):
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
                call .ytm_process_audio_info(raw_search_request, add_to_search_hist=True, add_to_audio_hist=True)
                if not _return:
                    jump .input_loop

            else:
                $ ytm_utils.add_search_history(
                    lower_search_request,
                    lower_search_request
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

                $ ytm_threading.update_thread_args(ytm_threading.search_music, [raw_search_request])
                call ytm_search_loop
                $ menu_list = _return

                label .menu_display:
                    if menu_list:
                        m 1eub "Alright! Look what I've found!"
                        show monika 1eua at t21
                        call screen mas_gen_scrollable_menu(menu_list, ytm_globals.SCR_MENU_AREA, ytm_globals.SCR_MENU_XALIGN, *ytm_globals.SCR_MENU_LAST_ITEMS)
                        show monika at t11

                        if isinstance(_return, ytm_utils.VideoInfo):
                            call .ytm_process_audio_info(_return.url, add_to_search_hist=False, add_to_audio_hist=True)
                            if not _return:
                                jump .menu_display

                        elif _return == ytm_globals.SCR_MENU_CHANGED_MIND:
                            if not ytm_globals.is_playing:
                                m 1eka "Oh...{w=0.2}{nw}"
                                extend 3ekb "I really love to listen to music with you!"
                                m 1eua "Let me know when you have time~"
                            else:
                                m 1eka "Oh, okay."

                        elif _return == ytm_globals.SCR_MENU_ANOTHER_SING:
                            m 1eub "Alright!"
                            jump .input_loop

                        else:
                            # aka the part you will never get to
                            m 2tfu "{cps=*2}Reading this doesn't seem like the best use of your time, [player].{/cps}{nw}"
                            $ _history_list.pop()

                    else:
                        m 1eud "Sorry, [mas_get_player_nickname(regex_replace_with_nullstr='my ')]...{w=0.5}I couldn't find anything."
                        m 3eua "Do you want to try again?{nw}"
                        $ _history_list.pop()
                        menu:
                            m "Do you want to try again?{fast}"

                            "Yes.":
                                jump .input_loop

                            "No.":
                                m 1eka "Oh, okay."

                    $ del menu_list

    $ del response_quips, response_quip, raw_search_request, lower_search_request
    return

label .ytm_process_audio_info(url, add_to_search_hist, add_to_audio_hist):
    show monika 1dsa
    window hide
    $ ytm_threading.update_thread_args(ytm_threading.get_audio_info, [url])
    call ytm_get_audio_info_loop
    $ audio_info = _return
    $ has_failed = False

    if audio_info:
        python:
            if add_to_search_hist:
                ytm_utils.add_search_history(audio_info.title, audio_info.url)
            if add_to_audio_hist:
                ytm_utils.add_audio_history(audio_info.url)

        if ytm_utils.does_cache_exist(audio_info.id):
            m 1dsa "Let me play that for us.{w=0.5}.{w=0.5}.{nw}"

            if ytm_utils.play_audio(ytm_globals.SHORT_MUSIC_DIRECTORY + audio_info.id + ytm_globals.EXTENSION, name=audio_info.title):
                m 1hua "There we go!"

            else:
                $ has_failed = True
                m 1ekd "Oh no...{w=0.5}something went wrong, [mas_get_player_nickname(regex_replace_with_nullstr='my ')]..."
                m 1euc "I'm sure we listened to this song before, but I can't seem to find it anymore..."
                # m 1eka "Let's try again later, alright?"

        else:
            if ytm_utils.should_cache_first(audio_info.size):
                m 3eub "We'll need to wait for a bit."
                m 1hua "I hope you don't mind, [mas_get_player_nickname()]~"
                $ ytm_threading.reset_thread(ytm_threading.download_and_notify)
                $ ytm_threading.update_thread_args(
                    ytm_threading.download_and_notify,
                    [
                        audio_info.url,
                        audio_info.title,
                        audio_info.size,
                        ytm_globals.FULL_MUSIC_DIRECTORY + audio_info.id + ytm_globals.EXTENSION
                    ]
                )
                $ ytm_threading.download_and_notify.start()

            else:
                m 1dsa "Let me just play that for us.{w=0.5}{nw}"
                $ ytm_threading.update_thread_args(
                    ytm_threading.download_and_play,
                    [audio_info.url, audio_info.id, audio_info.title, audio_info.size, True]
                )
                call ytm_play_audio_loop

                if _return:
                    m 1hua "There we go!"

                else:
                    $ has_failed = True
                    m 1eud "Something went wrong, [player]..."
                    # m 1eua "Let's try again later, alright?"

    else:
        $ has_failed = True
        m 1ekd "I'm sorry, [player]...{w=0.2}maybe I did something wrong..."# But she knows it's either your or youtube's fail
        m 1ekc "I can't play this song right now."
        # m 1eka "Let's try again later, okay?"

    if has_failed:
        m 3eka "Do you want to try again?{nw}"
        $ _history_list.pop()
        menu:
            m "Do you want to try again?{fast}"

            "Yes.":
                # Try again
                window auto
                $ del audio_info, has_failed
                return False

            "No.":
                m 1eka "Oh, okay."

    # Successfully downloaded OR failed and don't want to try again
    window auto
    $ del audio_info, has_failed
    return True


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
        $ ytm_utils.play_audio(ytm_globals.audio_to_queue["path"], name=ytm_globals.audio_to_queue["title"])

    else:
        m 3eua "Oh, looks like your song finished downloading."
        m 1dsa "Let me just play it for us.{w=0.5}.{w=0.5}.{nw}"
        $ ytm_utils.play_audio(ytm_globals.audio_to_queue["path"], name=ytm_globals.audio_to_queue["title"])

        if renpy.random.randint(1, 10) == 1:
            $ current_time = datetime.datetime.now().time()

            show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
            if mas_isAnytoMN(current_time, 17, 45):
                m 5eubla "Let's have another nice evening together~"

            elif mas_isAnytoN(current_time, 5, 45):
                m 5eubla "I'm glad we can relax a little before the day begins~"

            else:
                $ renpy.pause(4.0, hard=True)

            $ del current_time

        else:
            m 1hua "There we go!"
    return "no_unlock"


label ytm_search_loop:
    if not ytm_globals.loop_count:
        $ ellipsis_count = 1
        $ ytm_threading.search_music.start()

    elif ytm_globals.loop_count > 2*30:# 2 loops ~1 second
        return None

    $ ytm_globals.loop_count += 1

    if not ytm_threading.search_music.done():
        if ellipsis_count == 3:
            $ _history_list.pop()
            m "Let me see what I can find.{fast}{w=0.5}{nw}"
            $ ellipsis_count = 1

        else:
            $ ellipsis_count += 1
            extend ".{w=0.5}{nw}"

        jump ytm_search_loop

    else:
        $ _history_list.pop()
        m "Let me see what I can find...{fast}{nw}"

        $ ytm_globals.loop_count = 0
        return ytm_threading.search_music.get()

label ytm_get_audio_info_loop:
    if not ytm_globals.loop_count:
        $ ytm_threading.get_audio_info.start()

    elif ytm_globals.loop_count > 2*30:
        return None

    $ ytm_globals.loop_count += 1

    if not ytm_threading.get_audio_info.done():
        pause 0.5
        jump ytm_get_audio_info_loop

    else:
        $ ytm_globals.loop_count = 0
        return ytm_threading.get_audio_info.get()

label ytm_play_audio_loop:
    if not ytm_globals.loop_count:
        $ ellipsis_count = 1
        $ ytm_threading.download_and_play.start()

    elif ytm_globals.loop_count > 2*30:
        return None

    $ ytm_globals.loop_count += 1

    if not ytm_threading.download_and_play.done():
        if ellipsis_count == 3:
            $ _history_list.pop()
            m "Let me just play that for us.{fast}{w=0.5}{nw}"
            $ ellipsis_count = 1

        else:
            $ ellipsis_count += 1
            extend ".{w=0.5}{nw}"

        jump ytm_play_audio_loop

    else:
        $ _history_list.pop()
        m "Let me just play that for us...{fast}{nw}"
        $ ytm_globals.loop_count = 0
        return ytm_threading.download_and_play.get()
