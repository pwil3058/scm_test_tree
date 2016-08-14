### Copyright (C) 2015 Peter Williams <pwil3058@gmail.com>
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
import sys
import collections

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GdkPixbuf

from ..config_data import APP_NAME

# find the icons directory
# first look in the source directory (so that we can run uninstalled)
_libdir = os.path.join(sys.path[0], "pixmaps")
if not os.path.exists(_libdir) or not os.path.isdir(_libdir):
    _TAILEND = os.path.join("share", "pixmaps", APP_NAME)
    _prefix = sys.path[0]
    while _prefix:
        _libdir = os.path.join(_prefix, _TAILEND)
        if os.path.exists(_libdir) and os.path.isdir(_libdir):
            break
        _prefix = os.path.dirname(_prefix)

APP_ICON = APP_NAME
APP_ICON_FILE = os.path.join(os.path.dirname(_libdir), APP_ICON + os.extsep + "png")
APP_ICON_PIXBUF = GdkPixbuf.Pixbuf.new_from_file(APP_ICON_FILE)


_FACTORY = Gtk.IconFactory()
_FACTORY.add_default()
_FACTORY.add(APP_ICON, Gtk.IconSet(APP_ICON_PIXBUF))

_PREFIX = APP_NAME + "_"

def _png_file_name(item_name):
    return os.path.join(_libdir, item_name[len(_PREFIX):] + os.extsep + 'png')

def make_pixbuf(name):
    return GdkPixbuf.Pixbuf.new_from_file(_png_file_name(name))

StockAlias = collections.namedtuple("StockAlias", ["name", "alias", "text"])

# Icons that are aliased to Gtk or other stock items
STOCK_INSERT = _PREFIX + "stock_insert"
STOCK_RENAME = _PREFIX + "stock_rename"

# Icons that have to be designed eventually (using GtK stock in the meantime)
_STOCK_ALIAS_LIST = [
    StockAlias(name=STOCK_INSERT, alias=Gtk.STOCK_ADD, text="_Insert"),
    StockAlias(name=STOCK_RENAME, alias=Gtk.STOCK_PASTE, text=""),
]

_STYLE = Gtk.Frame().get_style()

for _item in _STOCK_ALIAS_LIST:
    _FACTORY.add(_item.name, _STYLE.lookup_icon_set(_item.alias))

#Gtk.stock_add([(item.name, item.text, 0, 0, None) for item in _STOCK_ALIAS_LIST])
