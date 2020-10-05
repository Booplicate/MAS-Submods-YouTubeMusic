
# YouTube Music

A submod which allows you to listen to music from youtube in the game. Compatible with [Night Music](https://github.com/multimokia/MAS-Submod-Nightmusic).

## Installation:
1. Make sure you're running the latest version of MAS.

2. Download the latest release of the submod from [the releases page](https://github.com/Booplicate/MAS-Submods-YouTubeMusic/releases/latest).

3. Now you need to extract files.

    - For Windows/Linux: Close the game and extract the content from the zip you downloaded into your `DDLC/` folder. Exactly this folder, you should have `DDLC.exe` and/or `DDLC.sh` there.

    - For Mac: The same as above, but after doing that you'll need to open `/lib/darwin-x86_64/lib/python2.7` and copy 2 files from there: `ssl.pyo` and `_ssl.so`. Then open `DDLC.app/Contents/MacOS/lib/darwin-x86_64/Lib` and paste the files there.

4. Optionally install [Paste](https://github.com/Legendkiller21/MAS-Submods/tree/master/Paste) (allows pasting links in the game) and/or [Submod Updater Plugin](https://github.com/Booplicate/MAS-Submods-SubmodUpdaterPlugin) (allows updating submods via in-game updater).

If you installed it correctly, your folders will look like this:
```
DDLC/game/
    python-packages/
        *a lot of different libs*
    Submods/
        Utilities/
            paste/
                paste.rpy
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
Monika will tell you everything in the game, just install the submod and launch the game. After her intro you can find the topic in the Music category.

## Limitations:
RenPy doesn't support live-streams, nothing I can do about it. ~~*Maybe one day I'll move the submod to another audio system.*~~
Currently YouTube playlists are not supported. I'm working on it, but it requires a lot of changes because of how RenPy handles audio.
