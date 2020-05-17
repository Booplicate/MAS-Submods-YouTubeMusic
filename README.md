
# YouTube Music

A submod which allows you to listen to music from youtube in the game. Compatible with [Night Music](https://github.com/multimokia/MAS-Submods/tree/NightMusic/Night%20Music). Works only on Windows. MacOS and Linux versions are in development.

## Installation:
0. Make sure you're running the latest version of MAS.

1. Download the latest release of the submod from [the releases page](https://github.com/Booplicate/MAS-Submods-YouTubeMusic/releases).

2. Close the game and extract the content from the zip you downloaded into your `DDLC/` folder. Exactly this folder, you should have `DDLC.exe` there.

3. Optionally install [Paste](https://github.com/Legendkiller21/MAS-Submods/tree/master/Paste) (allows you to paste links in the game).

If you installed it correctly, your folders will look like this:
```
DDLC/game/
    python-packages/
        *a lot of different libs*
    Submods/
        Utilities/
            paste/
                paste.rpy
        YouTube Music/
            temp/
            ytm_main.rpy
            ytm_overrides.rpy
            ytm_topics.rpy
            ytm_utils.rpy
```

## Usage:
Monika will tell you everything in the game, just install the submod and launch the game. After her intro you can find the topic in the Music category.

## Limitations:
RenPy doesn't support live-streams, nothing I can do about it. ~~*Maybe one day I'll move the submod to another audio system.*~~
Currently YouTube playlists are not supported. I'm working on it, but it requires a lot of changes because of how RenPy handles audio.
