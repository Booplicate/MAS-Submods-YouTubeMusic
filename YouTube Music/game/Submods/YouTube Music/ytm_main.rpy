
# Register the submod
init -990 python:
    store.mas_submod_utils.Submod(
        author="Booplicate",
        name="YouTube Music",
        description=(
            "A submod which allows you to listen to music from YouTube in the game. "
            "Monika searches songs by names, but you can also give her direct youtube links.\n"
            "Recommended to use {a=https://github.com/Legendkiller21/MAS-Submods/tree/master/Paste}{i}{u}Paste{/u}{/i}{/a} for copying/pasting links.\n"
            "Fully compatible with {a=https://github.com/multimokia/MAS-Submods/tree/NightMusic/Night%20Music}{i}{u}Nightmusic{/u}{/i}{/a}."
        ),
        version="2.6",
        settings_pane="ytm_settings_pane",
        version_updates={}
    )

# Register the updater
init -989 python:
    if store.mas_submod_utils.isSubmodInstalled("Submod Updater Plugin"):
        store.sup_utils.SubmodUpdater(
            submod="YouTube Music",
            user_name="Booplicate",
            repository_name="MAS-Submods-YouTubeMusic",
            update_dir=""
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
        ypos 0
        xfill True
        xmaximum 800
        style_prefix "check"

        hbox:
            text "Status: [connection]"

            if not store.ytm_globals.has_connection:
                if _tooltip is not None:
                    textbutton "(test connection)":
                        pos (-20, 1)
                        action Function(test_connection)
                        hovered SetField(_tooltip, "value", "Press to force checking your connection")
                        unhovered SetField(_tooltip, "value", _tooltip.default)

                else:
                    textbutton "(test connection)":
                        pos (-20, 1)
                        action Function(test_connection)

        if curr_track:
            text "Current track: [curr_track]"

screen ytm_history_submenu(animate=True):
    default settings = {"animate": animate}

    style_prefix "scrollable_menu"

    fixed:
        if settings["animate"]:
            at ytm_menu_slide

        area (410, 315, 440, 220)

        viewport:
            id "viewport"
            yfill False
            mousewheel True

            vbox:
                for button_prompt, input_value in reversed(store.ytm_globals.search_history):
                    textbutton button_prompt:
                        xpos 20
                        xsize 420
                        selected False
                        action Function(store.ytm_screen_utils.setParentInputValue, input_value)

        bar:
            style "classroom_vscrollbar"
            value YScrollValue("viewport")
            xalign 0.005

screen ytm_input_screen(prompt):
    default ytm_input = store.ytm_screen_utils.YTMInputValue()

    on "hide" action Function(store.ytm_screen_utils.toggleChildScreenAnimation, False)

    style_prefix "input"

    window:
        vbox:
            align (0.5, 0.5)
            spacing 5
            ypos -263
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
        alpha 0.0
        crop (0.0, 1.0, 1.0, 1.0)
        parallel:
            easein 0.2 crop (0.0, 0.0, 1.0, 1.0)
        parallel:
            easein 0.2 alpha 1.0

    on hide:
        alpha 1.0
        crop (0.0, 0.0, 1.0, 1.0)
        alpha 0.0
        parallel:
            easeout 0.2 crop (0.0, 1.0, 1.0, 1.0)
        parallel:
            easeout 0.2 alpha 0.0
