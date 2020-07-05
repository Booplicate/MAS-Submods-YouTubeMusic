
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
        version="2.2",
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
            curr_track = None

        # wrapper
        def test_connection():
            store.ytm_utils.isOnline(True)

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

        if curr_track:
            text "Current track: [curr_track]"

        # label "Maximum audio size to play from RAM: {0} MB".format(persistent._ytm_audio_size_limit)
        # bar value FieldValue(persistent, "_ytm_audio_size_limit", range=47, max_is_zero=False, style="slider", offset=3, step=1)

        # label "Maximum search results: {0} videos".format(persistent._ytm_search_limit)
        # bar value FieldValue(persistent, "_ytm_search_limit", range=25, max_is_zero=False, style="slider", offset=5, step=1)

screen ytm_history_submenu(animate=True):
    python:
        def _calculateMenuHeight():
            total_songs = len(store.ytm_globals.search_history)

            if total_songs > 2:
                factor = 45
            elif total_songs == 2:
                factor = 46
            else:
                factor = 47

            height = total_songs * factor

            return height if height <= 180 else 180

        def _calculateButtonsProps():
            total_songs = len(store.ytm_globals.search_history)

            if total_songs > 4:
                xpos = 20
                xsize = 400
            else:
                xpos = 0
                xsize = 420

            return (xpos, xsize)

        def _setParentInputValue(new_input):
            """
            A wrapper which allows us to do the magic in local env

            IN:
                new_input - a new value for input
            """
            _screen = renpy.get_screen("ytm_input_screen")
            if _screen:
                ytm_input = _screen.scope.get("ytm_input")
                ytm_input.set_text(new_input)

    default settings = {"animate": animate}
    default _height = _calculateMenuHeight()
    default xpos_xsize_tuple = _calculateButtonsProps()

    style_prefix "scrollable_menu"

    frame:
        if settings["animate"]:
            at ytm_menu_slide
        # 430, 340, 420, ???
        area (430, 310, 420, _height)
        # FIXME: better use my own styles in case the devs make changes for MAS ones
        style "mas_extra_menu_frame"

        viewport:
            id "viewport"
            yfill False
            mousewheel True

            vbox:
                for button_prompt, input_value in reversed(store.ytm_globals.search_history):
                    textbutton button_prompt:
                        xpos xpos_xsize_tuple[0]
                        xsize xpos_xsize_tuple[1]
                        selected False
                        action Function(_setParentInputValue, input_value)

        bar:
            style "classroom_vscrollbar"
            value YScrollValue("viewport")
            xalign 0.005

screen ytm_input_screen(prompt):
    python:
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

        def _toggleChildScreenAnimation(new_value):
            """
            This allows us to hide the sub-menu w/o animation
            when we need it to just disappear immediately

            IN:
                new_value - a bool to switch the setting
            """
            _screen = renpy.get_screen("ytm_history_submenu")
            if _screen:
                _settings = _screen.scope.get("settings", {})
                _settings["animate"] = new_value

    default ytm_input = YTMInputValue()

    on "hide" action Function(_toggleChildScreenAnimation, False)

    style_prefix "input"

    window:
        vbox:
            align (0.5, 0.5)
            spacing 5
            ypos -270
            style_prefix "choice"

            textbutton _("Nevermind."):
                selected False
                action Return("")

            if store.ytm_globals.search_history:
                if renpy.get_screen("ytm_history_submenu") is None:
                    textbutton _("Previous tracks."):
                        selected False
                        action ShowTransient("ytm_history_submenu")

                else:
                    textbutton _("Hide."):
                        selected False
                        action Hide("ytm_history_submenu")

        vbox:
            align (0.5, 0.5)
            spacing 30

            text prompt style "input_prompt"
            input:
                id "input"
                value ytm_input

transform ytm_menu_slide:
    crop_relative True
    yanchor 0
    on show:
        alpha 0.1
        crop (0.0, 1.0, 1.0, 1.0)
        easein 0.4 crop (0.0, 0.0, 1.0, 1.0) alpha 1.0
        # parallel:
        #     easein 0.4 crop (0.0, 0.0, 1.0, 1.0)
        # parallel:
        #     linear 0.45 alpha 1.0
    on hide:
        alpha 1.0
        crop (0.0, 0.0, 1.0, 1.0)
        easeout 0.4 crop (0.0, 1.0, 1.0, 1.0) alpha 0.1
        # parallel:
        #     easeout 0.4 crop (0.0, 1.0, 1.0, 1.0)
        # parallel:
        #     linear 0.35 alpha 0.0

# Updates go here
# label booplicate_youtube_music_v2_0(version="v2_0"):
#     return
# label booplicate_youtube_music_v2_1(version="v2_1"):
#     return