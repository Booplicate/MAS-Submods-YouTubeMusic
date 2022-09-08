
# Overrides
init 100:
    # General overrides
    python:
        store.mas_submod_utils.registerFunction("quit", ytm_utils.cleanup)
        store.mas_submod_utils.registerFunction("mas_o31_autoload_check", ytm_utils.check_o31_spook)
        store.songs.PAUSE = "Pause"
        store.songs.UNPAUSE = "Play"
        store.songs.FP_PAUSE = "pause"
        store.songs.FP_UNPAUSE = "unpause"

    # Overrides for vanilla MAS
    if not store.mas_submod_utils.isSubmodInstalled("Nightmusic"):
        python:
            def play_song(song, fadein=0.0, loop=True, set_per=False, fadeout=0.0, if_changed=False, **kwargs):
                """
                For docs look for the og func :P
                """
                ytm_flag = False

                if song is None:
                    song = songs.FP_NO_SONG
                    renpy.music.stop(channel="music", fadeout=fadeout)

                elif song is store.songs.FP_PAUSE:
                    renpy.music.set_pause(True)
                    ytm_flag = True

                elif song is store.songs.FP_UNPAUSE:
                    renpy.music.set_pause(False)
                    ytm_flag = True

                else:
                    renpy.music.play(
                        song,
                        channel="music",
                        loop=loop,
                        synchro_start=True,
                        fadein=fadein,
                        fadeout=fadeout,
                        if_changed=if_changed
                    )

                if not ytm_flag:
                    store.ytm_globals.is_playing = False

                    songs.current_track = song
                    songs.selected_track = song

                    if set_per:
                        persistent.current_track = song

            def select_music(**kwargs):
                """
                No docs for this one tho
                """
                # check for open menu
                if songs.enabled and not songs.menu_open:
                    # disable unwanted interactions
                    mas_RaiseShield_mumu()
                    # music menu label
                    selected_track = renpy.call_in_new_context("display_music_menu")

                    if selected_track == songs.NO_SONG:
                        selected_track = songs.FP_NO_SONG
                    elif selected_track == songs.PAUSE:
                        selected_track = songs.FP_PAUSE
                    elif selected_track == songs.UNPAUSE:
                        selected_track = songs.FP_UNPAUSE

                    # workaround to handle new context
                    if selected_track != songs.current_track:
                        play_song(selected_track, set_per=True)

                    # unwanted interactions are no longer unwanted
                    if store.mas_globals.dlg_workflow:
                        # the dialogue workflow means we should only enable
                        # music menu interactions
                        mas_MUMUDropShield()
                    elif store.mas_globals.in_idle_mode:
                        # to idle
                        mas_mumuToIdleShield()
                    else:
                        # otherwise we can enable interactions normally
                        mas_DropShield_mumu()

        screen music_menu(music_page, page_num=0, more_pages=False):
            modal True

            $ import store.songs as songs

            # logic to ensure Return works
            if songs.current_track is None:
                $ return_value = songs.NO_SONG
            else:
                $ return_value = songs.current_track

            #Allows the music menu to quit using hotkey
            key "noshift_M" action Return(return_value)
            key "noshift_m" action Return(return_value)

            zorder 200

            style_prefix "music_menu"

            frame:
                style "music_menu_outer_frame"

                hbox:
                    frame:
                        style "music_menu_navigation_frame"

                    frame:
                        style "music_menu_content_frame"

                        transclude

                vbox:
                    style_prefix "music_menu"

                    xpos gui.navigation_xpos
            #        yalign 0.4
                    spacing gui.navigation_spacing

                    # wonderful loop so we can dynamically add songs
                    for name,song in music_page:
                        textbutton _(name) action Return(song)
            vbox:
                yalign 1.0

                hbox:
                    # dynamic prevous text, so we can keep button size alignments
                    if page_num > 0:
                        textbutton _("<<<< Prev"):
                            style "music_menu_prev_button"
                            action Return(page_num - 1)

                    else:
                        textbutton _( " "):
                            style "music_menu_prev_button"
                            sensitive False

                    if more_pages:
                        textbutton _("Next >>>>"):
                            style "music_menu_return_button"
                            action Return(page_num + 1)

                textbutton _(songs.NO_SONG):
                    style "music_menu_return_button"
                    action Return(songs.NO_SONG)

                if store.ytm_globals.is_playing:
                    if not renpy.music.get_pause():
                        textbutton _(songs.PAUSE):
                            style "music_menu_return_button"
                            action Return(songs.PAUSE)
                    else:
                        textbutton _(songs.UNPAUSE):
                            style "music_menu_return_button"
                            action Return(songs.UNPAUSE)

                textbutton _("Return"):
                    style "music_menu_return_button"
                    action Return(return_value)

            label "Music Menu"

    # Special overrides for Nightmusic
    else:
        python:
            def play_song(song, fadein=0.0, loop=True, set_per=False, if_changed=True, is_nightmusic=False, fadeout=0.0, **kwargs):
                """
                Literally just plays a song onto the music channel
                Also sets the current track
                IN:
                    song - song to play. If None, the channel is stopped
                    fadein - number of seconds to fade in the song
                    loop - True if we should loop the song if possible, False to not loop.
                    set_per - True if we should set persistent track, False if not
                    if_changed - True if we should change if the song is different, False otherwise (default True)
                    is_nightmusic - True if this is nightmusic and we should set vars accordingly (prevents crashes)
                    fadeout - Amount of time it takes to fade out a track (if you play None)
                """
                ytm_flag = False

                if song is None:
                    song = store.songs.FP_NO_SONG
                    renpy.music.stop(channel="music", fadeout=fadeout)

                elif song is store.songs.FP_PAUSE:
                    renpy.music.set_pause(True)
                    ytm_flag = True

                elif song is store.songs.FP_UNPAUSE:
                    renpy.music.set_pause(False)
                    ytm_flag = True

                elif song is store.songs.FP_NIGHTMUSIC:
                    #Run a nightmusic alg for this
                    song = store.nm_utils.pickSong(nm_utils.nightMusicStation)
                    is_nightmusic = True

                if not ytm_flag:
                    #Now play a song
                    renpy.music.play(
                        song,
                        channel="music",
                        loop=loop,
                        synchro_start=True,
                        fadein=fadein,
                        fadeout=fadeout,
                        if_changed=if_changed
                    )

                    store.ytm_globals.is_playing = False

                    if is_nightmusic:
                        songs.current_track = store.songs.FP_NIGHTMUSIC
                        songs.selected_track= store.songs.FP_NIGHTMUSIC
                    else:
                        songs.current_track = song
                        songs.selected_track = song

                    if set_per:
                        persistent.current_track = song

            def select_music(**kwargs):
                # check for open menu
                if songs.enabled and not songs.menu_open:

                    # disable unwanted interactions
                    mas_RaiseShield_mumu()

                    # music menu label
                    selected_track = renpy.call_in_new_context("display_music_menu_ov")

                    if selected_track == songs.NO_SONG:
                        selected_track = songs.FP_NO_SONG
                    elif selected_track == songs.PAUSE:
                        selected_track = songs.FP_PAUSE
                    elif selected_track == songs.UNPAUSE:
                        selected_track = songs.FP_UNPAUSE

                    # workaround to handle new context
                    if selected_track == songs.FP_NIGHTMUSIC:
                        #Set up the file list
                        song_files = nm_utils.getSongs(nm_utils.nightMusicStation, with_filepaths=True)

                        #Ensure list actually has things in it
                        if len(song_files) > 0:
                            #Playlist mode will play all songs
                            if persistent._music_playlist_mode:
                                renpy.random.shuffle(song_files)
                                play_song(song_files, is_nightmusic=True)

                            #We just want it in single song mode
                            else:
                                song = random.choice(song_files)
                                play_song(song, is_nightmusic=True)

                    elif selected_track != songs.current_track:
                        play_song(selected_track, set_per=True)

                    # unwanted interactions are no longer unwanted
                    if store.mas_globals.dlg_workflow:
                        # the dialogue workflow means we should only enable
                        # music menu interactions
                        mas_MUMUDropShield()

                    elif store.mas_globals.in_idle_mode:
                        # to idle
                        mas_mumuToIdleShield()

                    else:
                        # otherwise we can enable interactions normally
                        mas_DropShield_mumu()

        screen music_menu_ov(music_page, page_num=0, more_pages=False):
            modal True

            $ import store.songs as songs

            # logic to ensure Return works
            if songs.current_track is None:
                $ return_value = songs.NO_SONG
            else:
                $ return_value = songs.current_track

            #Logic to fix looping upon exiting the music menu
            if (
                store.songs.current_track == store.songs.FP_NIGHTMUSIC
                or store.songs.current_track and "nightmusic" in store.songs.current_track
            ):
                if not persistent._music_playlist_mode:
                    $ return_key = nm_utils.getPlayingSong(filepath=True)
                else:
                    $ return_key = store.songs.FP_NIGHTMUSIC
            else:
                $ return_key = return_value

            #Allows the music menu to quit using hotkey
            key "noshift_M" action Return(return_key)
            key "noshift_m" action Return(return_key)

            zorder 200

            style_prefix "music_menu"

            frame:
                hbox:
                    # dynamic prevous text, so we can keep button size alignments
                    if page_num > 0:
                        textbutton _("<<<< Prev"):
                            style "music_menu_prev_button"
                            action Return(page_num - 1)

                    else:
                        textbutton _( " "):
                            style "music_menu_prev_button"
                            sensitive False

                    if more_pages:
                        textbutton _("Next >>>>"):
                            style "music_menu_return_button"
                            action Return(page_num + 1)

                style "music_menu_outer_frame"

                hbox:

                    frame:
                        style "music_menu_navigation_frame"

                    frame:
                        style "music_menu_content_frame"

                        transclude

                # this part copied from navigation menu
                vbox:
                    style_prefix "music_menu"

                    xpos gui.navigation_xpos
            #        yalign 0.4
                    spacing gui.navigation_spacing

                    # wonderful loop so we can dynamically add songs
                    for name,song in music_page:
                        textbutton _(name) action Return(song)

                    vbox:
                        style_prefix "check"
                        textbutton _("Playlist Mode"):
                            action [ToggleField(persistent, "_music_playlist_mode"), Function(nm_utils.modeChange)]
                            selected persistent._music_playlist_mode
            vbox:
                yalign 1.0

                textbutton _(songs.NO_SONG):
                    style "music_menu_return_button"
                    action Return(songs.NO_SONG)

                if store.ytm_globals.is_playing:
                    if not renpy.music.get_pause():
                        textbutton _(songs.PAUSE):
                            style "music_menu_return_button"
                            action Return(songs.PAUSE)
                    else:
                        textbutton _(songs.UNPAUSE):
                            style "music_menu_return_button"
                            action Return(songs.UNPAUSE)

                textbutton _("Return"):
                    style "music_menu_return_button"
                    if (
                        store.songs.current_track == store.songs.FP_NIGHTMUSIC
                        or store.songs.current_track and "nightmusic" in store.songs.current_track
                    ):
                        if not persistent._music_playlist_mode:
                            action Return(nm_utils.getPlayingSong(filepath=True))
                        else:
                            action Return(store.songs.FP_NIGHTMUSIC)
                    else:
                        action Return(return_value)

            label "Music Menu"


python early:
    import os

    @property
    def ytm_stdio_redirector_encoding(self):
        """
        Implements the encoding property
        """
        if hasattr(self.real_file, "encoding"):
            return self.real_file.encoding
        return None

    def ytm_stdio_redirector_isatty(self):
        """
        Implements the isatty method
        """
        if hasattr(self.real_file, "isatty"):
            return self.real_file.isatty()
        return NotImplemented

    def ytm_stdio_redirector_fileno(self):
        """
        Implements the fileno method
        """
        if hasattr(self.real_file, "fileno"):
            return self.real_file.fileno()
        return NotImplemented

    if not "RENPY_NO_REDIRECT_STDIO" in os.environ:
        # This only relevant to r7
        if hasattr(renpy.exports.renpy.log, "StdioRedirector"):
            renpy.exports.renpy.log.StdioRedirector.encoding = ytm_stdio_redirector_encoding
            renpy.exports.renpy.log.StdioRedirector.isatty = ytm_stdio_redirector_isatty
            renpy.exports.renpy.log.StdioRedirector.fileno = ytm_stdio_redirector_fileno
