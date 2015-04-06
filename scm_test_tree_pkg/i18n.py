import os, sys
import locale
import gettext

from scm_test_tree_pkg.config_data import APP_NAME

# find the locale directory
# first look in the source directory (so that we can run uninstalled)
LOCALE_DIR = os.path.join(sys.path[0], 'i10n')
if not os.path.exists(LOCALE_DIR) or not os.path.isdir(LOCALE_DIR):
    # if we get here it means we're installed and we assume that the
    # locale files were installed under the same prefix as the
    # application.
    _TAILEND = os.path.join('share', 'locale')
    _prefix = sys.path[0]
    _last_prefix = None # needed to prevent possible infinite loop
    while _prefix and _prefix != _last_prefix:
        LOCALE_DIR = os.path.join(_prefix, _TAILEND)
        if os.path.exists(LOCALE_DIR) and os.path.isdir(LOCALE_DIR):
            break
        _last_prefix = _prefix
        _prefix = os.path.dirname(_prefix)
    # As a last resort, try the usual place
    if not (os.path.exists(LOCALE_DIR) and os.path.isdir(LOCALE_DIR)):
        LOCALE_DIR = os.path.join(sys.prefix, 'share', 'locale')

# Lets tell those details to gettext
gettext.install(APP_NAME, localedir=LOCALE_DIR)
