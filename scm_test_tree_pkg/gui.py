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

import gtk

from scm_test_tree_pkg import ifce
from scm_test_tree_pkg import dialogue
from scm_test_tree_pkg import ws_actions
from scm_test_tree_pkg import recollect
from scm_test_tree_pkg import icons
from scm_test_tree_pkg import file_tree

class MainWindow(gtk.Window, dialogue.BusyIndicator, ws_actions.AGandUIManager):
    count = 0
    def __init__(self):
        assert MainWindow.count == 0
        MainWindow.count += 1
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.parse_geometry(recollect.get("main_window", "last_geometry"))
        self.set_icon_from_file(icons.APP_ICON_FILE)
        dialogue.BusyIndicator.__init__(self)
        self.connect("destroy", self._quit)
        dialogue.init(self)
        ws_actions.AGandUIManager.__init__(self)
        self.connect("configure_event", self._configure_event_cb)
        self.add(file_tree.FileTreeWidget())
    def populate_action_groups(self):
        pass
    def _quit(self, _widget):
        gtk.main_quit()
    def _configure_event_cb(self, widget, event):
        recollect.set("main_window", "last_geometry", "{0.width}x{0.height}+{0.x}+{0.y}".format(event))
