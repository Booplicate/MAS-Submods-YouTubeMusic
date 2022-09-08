
# YouTube Music

A submod which allows you to listen to music from youtube in the game. Compatible with [Night Music](https://github.com/multimokia/MAS-Submod-Nightmusic).

## Installation:
1. Make sure you're running the latest version of MAS.

2. Download the latest release of the submod from [the releases page](https://github.com/Booplicate/MAS-Submods-YouTubeMusic/releases/latest).

3. Close the game
    - **Only for Windows and Linux**: extract the content from the zip you downloaded into your `DDLC/` folder. Exactly this folder, you should have `DDLC.exe` and/or `DDLC.sh` there.

    - **Only for Mac**: extract the content from the zip you downloaded into your `autorun/` folder within `DDLC.app`. Exactly this folder, you should have `DDLC.sh` there.

If you installed everything correctly, your folders will look like this (on win/linux):
```
DDLC/game/
    python-packages/
        *a lot of different libs*
    Submods/
        Submod Updater Plugin/
            *some assets*
            submod_updater_plugin.rpy
        YouTube Music/
            temp/
            ytm_main.rpy
            ytm_overrides.rpy
            ytm_topics.rpy
            ytm_utils.rpy
```

## Usage:
Monika will tell you everything in the game, just install the submod and launch the game. After her intro you can find the topic in the Music category. You can bookmark the topic by pressing `b` during the conversation.

## Limitations:
RenPy doesn't support live-streams, and quite bad handles playlists. Hence those require a lot of changes to the audio system.
