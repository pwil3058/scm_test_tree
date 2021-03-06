### Copyright (C) 2005-2016 Peter Williams <pwil3058@gmail.com>
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

import os
import fnmatch
import collections

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk

from ..bab import utils

from ..gtx import gutils
from ..gtx import tlview
from ..gtx import table
from ..gtx import dialogue
from ..gtx import actions
from ..gtx import apath

from .. import CONFIG_DIR_PATH

from . import ifce
from . import icons

SAVED_TGND_FILE_PATH = os.sep.join([CONFIG_DIR_PATH, "testgrounds"])

class TGndPathView(apath.AliasPathView):
    SAVED_FILE_NAME = SAVED_TGND_FILE_PATH

class TGndPathTable(apath.AliasPathTable):
    VIEW = TGndPathView

class TGndOpenDialog(apath.PathSelectDialog):
    PATH_TABLE = TGndPathTable
    def __init__(self, parent=None):
        apath.PathSelectDialog.__init__(self, label=_("Workspace/Directory"), parent=parent)

def generate_testground_menu():
    return TGndPathView.generate_alias_path_menu(_("Test Grounds"), lambda newtgnd: ifce.chdir(newtgnd))
