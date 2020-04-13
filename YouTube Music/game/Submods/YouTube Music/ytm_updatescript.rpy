
# A one-time update script since we didn't have the framework back then
init 998 python:
    ytm_fixPersistent()

init 999 python:
    store.mas_utils.trydel(renpy.config.basedir + "/" + renpy.get_filename_line()[0], True)
    store.mas_utils.trydel(renpy.config.basedir + "/" + renpy.get_filename_line()[0] + 'c', True)