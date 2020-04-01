
# A one-time update script since we didn't have the framework back then
init 998 python:
    # if "ytm_monika_find_music.ytm_process_audio_info" in persistent._seen_ever:
    #     persistent._seen_ever.pop("ytm_monika_find_music.ytm_process_audio_info")

    ytm_fixPersistent()

init 999 python:
    store.mas_utils.trydel(renpy.config.basedir + "/" + renpy.get_filename_line()[0], True)
    store.mas_utils.trydel(renpy.config.basedir + "/" + renpy.get_filename_line()[0] + 'c', True)