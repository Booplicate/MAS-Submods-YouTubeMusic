
# Overrides
init 100:
    # General overrides
    python:
        store.mas_submod_utils.registerFunction("quit", ytm_utils.cleanUp)
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

init -999 python:
    import os
    os.environ["SSL_CERT_FILE"] = renpy.config.gamedir + "/python-packages/certifi/cacert.pem"

# AudioData support for RenPy 6.99.12
python early:
    import io

    class AudioData(unicode):
        """
        :doc: audio

        This class wraps a bytes object containing audio data, so it can be
        passed to the audio playback system. The audio data should be contained
        in some format Ren'Py supports. (For examples RIFF WAV format headers,
        not unadorned samples.)

        `data`
            A bytes object containing the audio file data.

        `filename`
            A synthetic filename associated with this data. It can be used to
            suggest the format `data` is in, and is reported as part of
            error messages.

        Once created, this can be used wherever an audio filename is allowed. For
        example::

            define audio.easteregg = AudioData(b'...', 'sample.wav')
            play sound easteregg
        """

        def __new__(cls, data, filename):
            rv = unicode.__new__(cls, filename)
            rv.data = data
            return rv

        def __init__(self, data, filename):
            self.filename = filename

        def __reduce__(self):
            # Pickle as a str is safer
            return (str, (self.filename, ))

    def ytm_periodic_override(self):
        """
        This is the periodic call that causes this channel to load new stuff
        into its queues, if necessary.
        """

        # Update the channel volume.
        vol = self.chan_volume * renpy.game.preferences.volumes[self.mixer]

        if vol != self.actual_volume:
            renpy.audio.renpysound.set_volume(self.number, vol)
            self.actual_volume = vol

        # This should be set from something that checks to see if our
        # mixer is muted.
        force_stop = self.context.force_stop or (renpy.game.preferences.mute[self.mixer] and self.stop_on_mute)

        if self.playing and force_stop:
            renpy.audio.renpysound.stop(self.number)
            self.playing = False
            self.wait_stop = False

        if force_stop:
            if self.loop:
                self.queue = self.queue[-len(self.loop):]
            else:
                self.queue = [ ]
            return

        # Should we do the callback?
        do_callback = False

        topq = None

        # This has been modified so we only queue a single sound file
        # per call, to prevent memory leaks with really short sound
        # files. So this loop will only execute once, in practice.
        while True:

            depth = renpy.audio.renpysound.queue_depth(self.number)

            if depth == 0:
                self.wait_stop = False
                self.playing = False

            # Need to check this, so we don't do pointless work.
            if not self.queue:
                break

            # If the pcm_queue is full, then we can't queue
            # anything, regardless of if it is midi or pcm.
            if depth >= 2:
                break

            # If we can't buffer things, and we're playing something
            # give up here.
            if not self.buffer_queue and depth >= 1:
                break

            # We can't queue anything if the depth is > 0 and we're
            # waiting for a synchro_start.
            if self.synchro_start and depth:
                break

            # If the queue is full, return.
            if renpy.audio.renpysound.queue_depth(self.number) >= 2:
                break

            # Otherwise, we might be able to enqueue something.
            topq = self.queue.pop(0)

            # Blacklist of old file formats we used to support, but we now
            # ignore.
            lfn = topq.filename.lower() + self.file_suffix.lower()
            for i in (".mod", ".xm", ".mid", ".midi"):
                if lfn.endswith(i):
                    topq = None

            if not topq:
                continue

            try:
                filename, start, end = self.split_filename(topq.filename, topq.loop)

                if (end >= 0) and ((end - start) <= 0) and self.queue:
                    continue

                if isinstance(topq.filename, AudioData):
                    topf = io.BytesIO(topq.filename.data)
                else:
                    topf = renpy.audio.audio.load(self.file_prefix + filename + self.file_suffix)

                renpy.audio.renpysound.set_video(self.number, self.movie)

                if depth == 0:
                    renpy.audio.renpysound.play(self.number, topf, topq.filename, paused=self.synchro_start, fadein=topq.fadein, tight=topq.tight, start=start, end=end)
                else:
                    renpy.audio.renpysound.queue(self.number, topf, topq.filename, fadein=topq.fadein, tight=topq.tight, start=start, end=end)

                self.playing = True

            except:

                # If playing failed, remove topq.filename from self.loop
                # so we don't keep trying.
                while topq.filename in self.loop:
                    self.loop.remove(topq.filename)

                if renpy.config.debug_sound and not renpy.game.after_rollback:
                    raise
                else:
                    return

            break

        if self.loop and not self.queue:
            for i in self.loop:
                if topq is not None:
                    newq = renpy.audio.audio.QueueEntry(i, 0, topq.tight, True)
                else:
                    newq = renpy.audio.audio.QueueEntry(i, 0, False, True)

                self.queue.append(newq)
        else:
            do_callback = True

        # Queue empty callback.
        if do_callback and self.callback:
            self.callback()  # E1102

        # global global_pause
        want_pause = self.context.pause or renpy.audio.audio.global_pause

        if self.paused != want_pause:

            if want_pause:
                self.pause()
            else:
                self.unpause()

            self.paused = want_pause

    renpy.audio.audio.Channel.periodic = ytm_periodic_override