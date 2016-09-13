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

import collections
import os
import os.path

from gi.repository import Gtk

from aipoed import enotify

from aipoed.gui import file_tree
from aipoed.gui import dialogue
from aipoed.gui import actions

from .. import cmd_ifce

from . import ws_actions
from . import icons

class ManagedFileTreeView(file_tree.FileTreeView, enotify.Listener, ws_actions.WSListenerMixin):
    DEFAULT_POPUP = "/stt_files_popup"
    UI_DESCR = \
    """
    <ui>
      <menubar name="files_menubar">
        <menu name="files_menu" action="menu_files">
         <menuitem action="refresh_files"/>
        </menu>
      </menubar>
      <popup name="files_popup">
          <menuitem action="delete_fs_items"/>
          <menuitem action="new_file"/>
        <separator/>
          <menuitem action="copy_fs_items"/>
          <menuitem action="move_fs_items"/>
          <menuitem action="rename_fs_item"/>
      </popup>
      <popup name="stt_files_popup">
          <menuitem action="stt_modify_selected_files"/>
          <menuitem action="stt_delete_fs_items"/>
          <menuitem action="stt_new_file"/>
        <separator/>
          <menuitem action="stt_copy_fs_items"/>
          <menuitem action="stt_move_fs_items"/>
          <menuitem action="stt_rename_fs_item"/>
      </popup>
    </ui>
    """
    AUTO_EXPAND = False
    DIRS_SELECTABLE = True
    ASK_BEFORE_DELETE = True
    OPEN_NEW_FILES_FOR_EDIT = False
    def __init__(self, **kwargs):
        file_tree.FileTreeView.__init__(self, **kwargs)
        enotify.Listener.__init__(self)
        ws_actions.WSListenerMixin.__init__(self)
    def populate_action_groups(self):
        self.action_groups[ws_actions.AC_IN_TGND|actions.AC_SELN_MADE].add_actions(
            [
                ("stt_modify_selected_files", Gtk.STOCK_EDIT, _('_Modify'), None,
                 _('Modify the selected file(s)'),
                 self.modify_selected_files_acb
                ),
                ("stt_copy_fs_items", Gtk.STOCK_COPY, _("Copy"), None,
                 _("Copy the selected file(s) and/or directories"),
                 lambda _action: self._move_or_copy_fs_items(True, self.get_selected_fsi_paths())
                ),
                ("stt_move_fs_items", Gtk.STOCK_PASTE, _("_Move/Rename"), None,
                 _("Move the selected file(s) and/or directories"),
                 lambda _action: self._move_or_copy_fs_items(False, self.get_selected_fsi_paths())
                ),
                ("stt_delete_fs_items", Gtk.STOCK_DELETE, _("_Delete"), None,
                 _("Delete the selected file(s) and/or directories"),
                 lambda _action=None: self.delete_selected_fs_items()
                ),
            ])
        self.action_groups[ws_actions.AC_IN_TGND|actions.AC_SELN_UNIQUE].add_actions(
           [
                ("stt_rename_fs_item", icons.STOCK_RENAME, _("Rename/Move"), None,
                 _("Rename/move the selected file or directory"),
                 lambda _action: self._move_or_copy_fs_item(False, self.get_selected_fsi_path())
                ),
            ])
        self.action_groups[ws_actions.AC_IN_TGND].add_actions(
            [
                ("stt_new_file", Gtk.STOCK_NEW, _("_New"), None,
                 _("Create a new file"),
                 lambda _action: self.create_new_file()
                ),
            ])
    def modify_selected_files_acb(self, _menu_item):
        self.report_any_problems(cmd_ifce.modify_files(self.get_selected_file_paths(), gui_calling=True))

class ManagedFileTreeWidget(file_tree.FileTreeWidget):
    MENUBAR = "/files_menubar"
    BUTTON_BAR_ACTIONS = ["show_hidden_files"]
    TREE_VIEW = ManagedFileTreeView
    SIZE = (240, 320)
