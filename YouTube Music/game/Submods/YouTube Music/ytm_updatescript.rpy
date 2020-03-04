
init 998 python:
    ytm_fixPersistent()

init 999 python:
    store.mas_utils.trydel(renpy.config.basedir + "/" + renpy.get_filename_line()[0])
    store.mas_utils.trydel(renpy.config.basedir + "/" + renpy.get_filename_line()[0] + 'c')