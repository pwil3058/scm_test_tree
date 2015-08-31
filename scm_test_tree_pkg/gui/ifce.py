### Copyright (C) 2007-2015 Peter Williams <pwil3058@gmail.com>
###
### This program is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; version 2 of the License only.
###
### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.
###
### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import sys
import collections
import os
import datetime

from ..cmd_result import CmdResult
from .. import config_data

from . import terminal
from . import ws_event
from . import recollect

E_CHANGE_WD = ws_event.new_event_flag()

in_valid_test_gnd = False

CURDIR = os.getcwd()

TERM = None
log = False

def get_test_tree_root(fdir=None):
    if not fdir:
        fdir = os.getcwd()
    root = fdir
    while True:
        from .. import ifce
        cf_path = os.path.join(root, ifce.COUNT_FILE)
        if os.path.exists(cf_path) and not os.path.isdir(cf_path):
            return root
        newroot = os.path.dirname(root)
        if root == newroot:
            break
        root = newroot
    return None

def init(start_dir=None):
    global TERM
    global CURDIR
    global in_valid_test_gnd
    if terminal.AVAILABLE:
        TERM = terminal.Terminal()
    base_dir = get_test_tree_root(start_dir)
    if base_dir is not None:
        from . import config
        os.chdir(base_dir)
        TERM.set_cwd(base_dir)
        config.TGndPathTable.append_saved_path(base_dir)
        in_valid_test_gnd = True
        recollect.set(config_data.APP_NAME, "last_pgnd", base_dir)
    else:
        in_valid_test_gnd = False
    CURDIR = os.getcwd()
    ws_event.notify_events(E_CHANGE_WD, new_wd=CURDIR)
    return CmdResult.ok()

def close():
    return CmdResult.ok()

def chdir(newdir=None):
    from .. import utils
    global CURDIR
    global in_valid_test_gnd
    old_wd = os.getcwd()
    retval = CmdResult.ok()
    if newdir:
        try:
            os.chdir(newdir)
        except OSError as err:
            import errno
            ecode = errno.errorcode[err.errno]
            emsg = err.strerror
            retval = CmdResult.error(stderr='%s: "%s" :%s' % (ecode, newdir, emsg))
    base_dir = get_test_tree_root()
    if base_dir is not None:
        from . import config
        os.chdir(base_dir)
        TERM.set_cwd(base_dir)
        config.TGndPathTable.append_saved_path(base_dir)
        in_valid_test_gnd = True
        recollect.set(config_data.APP_NAME, "last_pgnd", base_dir)
    else:
        in_valid_test_gnd = False
    curdir = os.getcwd()
    if not utils.samefile(curdir, CURDIR):
        if TERM:
            TERM.set_cwd(curdir)
    CURDIR = curdir
    ws_event.notify_events(E_CHANGE_WD, new_wd=CURDIR)
    return retval

def check_interfaces(args):
    from .. import utils
    global CURDIR
    curdir = os.getcwd()
    if not utils.samefile(CURDIR, curdir):
        args["new_wd"] = curdir
        CURDIR = curdir
        return E_CHANGE_WD # don't send ifce changes and wd change at the same time
    return 0
