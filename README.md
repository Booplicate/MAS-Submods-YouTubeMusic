
# YouTube Music

A submod which allows you to listen to music from youtube in the game. Compatible with [Night Music](https://github.com/multimokia/MAS-Submods/tree/NightMusic/Night%20Music). Works only on Windows. It could work on Mac/Linux, but since I don't have these installed, I won't add support to them. If you're willing to help me with testing on those systems, let me know (can open an issue).
The submod is tested to work with MAS v0.11.0+ (both stable/unstable)

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
                paste.rpyc
        YouTube Music/
            temp/
            ytm_overrides.rpyc
            ytm_topics.rpyc
            ytm_utils.rpyc
```

## Usage:
Monika will tell you everything in the game, just install the submod and launch the game. After her intro you can find the topic in the Music category.

## Limitations:
RenPy doesn't support live-streams, nothing I can do about it. ~~*Maybe one day I'll move the submod to another audio system.*~~
Currently YouTube playlists are not supported. I'm working on it, but it requires a lot of changes because of how RenPy handles audio.
