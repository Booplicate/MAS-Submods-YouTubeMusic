
# TODO: uncomment when the time comes
# Also why not to use a single dict for settings
# Default persistent vars
# init -20:
#     # Maximum audio size to play from RAM (bytes)
#     default persistent._ytm_audio_size_limit = 15
#     # Maximum search results
#     default persistent._ytm_search_limit = 15

# Register the submod
init -990 python in mas_submod_utils:
    Submod(
        author="Booplicate",
        name="YouTube Music",
        description="A submod which allows you to listen to music from youtube in the game. Compatible with Night Music.",
        version="2.0",
        settings_pane="ytm_settings_pane",
        version_updates={}
    )

# Define our settings screen
screen ytm_settings_pane():
    vbox:
        box_wrap False
        xfill True
        xmaximum 570
        style_prefix mas_ui.cbx_style_prefix

        if store.ytm_globals.has_connection is True:
            $ connection = "online"

        elif store.ytm_globals.has_connection is False:
            $ connection = "offline"

        else:
            $ connection = "unknown"

        text "Status: [connection]"
        # textbutton _("Test connection"):
        #     style mas_ui.nm_button_style
        #     action Function(ytm_isOnline, True)

        # label "Maximum audio size to play from RAM: {0} MB".format(persistent._ytm_audio_size_limit)
        # bar value FieldValue(persistent, "_ytm_audio_size_limit", range=47, max_is_zero=False, style="slider", offset=3, step=1)

        # label "Maximum search results: {0} videos".format(persistent._ytm_search_limit)
        # bar value FieldValue(persistent, "_ytm_search_limit", range=25, max_is_zero=False, style="slider", offset=5, step=1)

# Updates go here
# label booplicate_youtube_music_v2_0(version="v2_0"):
#     return