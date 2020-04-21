
# Default persistent vars
# init -20:
#     # NOTE: if I ever decide to use persistent, I'd use a single dict for settings
#     # Maximum audio size to play from RAM (bytes)
#     default persistent._ytm_audio_size_limit = 15
#     # Maximum search results
#     default persistent._ytm_search_limit = 15

# Register the submod
init -990 python in mas_submod_utils:
    Submod(
        author="Booplicate",
        name="YouTube Music",
        description=(
            "A submod which allows you to listen to music from YouTube in the game. "
            "Monika searches songs by names, but you can also give her links. "
            "Recommended to use {a=https://github.com/Legendkiller21/MAS-Submods/tree/master/Paste}{i}{u}Paste{/u}{/i}{/a} for copying/pasting links.\n"
            "Compatible with {a=https://github.com/multimokia/MAS-Submods/tree/NightMusic/Night%20Music}{i}{u}Nightmusic{/u}{/i}{/a}."
        ),
        version="2.1",
        settings_pane="ytm_settings_pane",
        version_updates={}
    )

# Define our settings screen
screen ytm_settings_pane():
    python:
        # tooltip
        submods_screen = store.renpy.get_screen("submods", "screens")

        if submods_screen:
            _tooltip = submods_screen.scope.get("tooltip", None)

        else:
            _tooltip = None

        # connection
        if store.ytm_globals.has_connection is True:
            connection = "Online"

        elif store.ytm_globals.has_connection is False:
            connection = "Offline"

        else:
            connection = "Unknown"

        # current song
        if (
            store.ytm_globals.is_playing
            and store.songs.current_track
        ):
            curr_track = store.songs.current_track

        elif store.songs.current_track == "nightmusic":
            curr_track = "Monika's choice~"

        elif store.songs.current_track:
            curr_track = store.songs.current_track.split("/")[-1].split(".")[0]

        else:
            curr_track = "Unknown"

        # wrapper
        def test_connection():
            store.ytm_isOnline(True)

    vbox:
        box_wrap False
        xfill True
        xmaximum 800
        style_prefix "check"

        hbox:
            text "Status: [connection]"

            if not store.ytm_globals.has_connection:
                if _tooltip:
                    textbutton "(test connection)":
                        xpos -20
                        ypos 1
                        action Function(test_connection)
                        hovered SetField(_tooltip, "value", "Press to force checking your connection")
                        unhovered SetField(_tooltip, "value", _tooltip.default)

                else:
                    textbutton "(test connection)":
                        xpos -20
                        ypos 1
                        action Function(test_connection)

        text "Current track: [curr_track]"

        # label "Maximum audio size to play from RAM: {0} MB".format(persistent._ytm_audio_size_limit)
        # bar value FieldValue(persistent, "_ytm_audio_size_limit", range=47, max_is_zero=False, style="slider", offset=3, step=1)

        # label "Maximum search results: {0} videos".format(persistent._ytm_search_limit)
        # bar value FieldValue(persistent, "_ytm_search_limit", range=25, max_is_zero=False, style="slider", offset=5, step=1)

# Updates go here
# label booplicate_youtube_music_v2_0(version="v2_0"):
#     return
# label booplicate_youtube_music_v2_1(version="v2_1"):
#     return