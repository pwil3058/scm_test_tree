### Copyright (C) 2005-2015 Peter Williams <pwil3058@gmail.com>

### This program is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; version 2 of the License only.

### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import collections
import os
import os.path

import gtk
import gobject
import pango

from .. import utils
from .. import cmd_result
from .. import fsdb
from .. import ifce

from . import tlview
from . import gutils
from . import actions
from . import ws_actions
from . import dialogue
from . import ws_event
from . import icons

def _check_if_force(result):
    return dialogue.ask_force_or_cancel(result) == dialogue.Response.FORCE

class FileTreeView(tlview.TreeView, ws_actions.AGandUIManager, ws_event.Listener, dialogue.BusyIndicatorUser):
    class Model(tlview.TreeView.Model):
        Row = collections.namedtuple('Row', ['name', 'is_dir', 'style', 'foreground', 'icon', 'status', 'related_file_str'])
        types = Row(
            name=gobject.TYPE_STRING,
            is_dir=gobject.TYPE_BOOLEAN,
            style=gobject.TYPE_INT,
            foreground=gobject.TYPE_STRING,
            icon=gobject.TYPE_STRING,
            status=gobject.TYPE_STRING,
            related_file_str=gobject.TYPE_STRING
        )
        def insert_place_holder(self, dir_iter):
            self.append(dir_iter)
        def insert_place_holder_if_needed(self, dir_iter):
            if self.iter_n_children(dir_iter) == 0:
                self.insert_place_holder(dir_iter)
        def recursive_remove(self, fsobj_iter):
            child_iter = self.iter_children(fsobj_iter)
            if child_iter != None:
                while self.recursive_remove(child_iter):
                    pass
            return self.remove(fsobj_iter)
        def depopulate(self, dir_iter):
            child_iter = self.iter_children(dir_iter)
            if child_iter != None:
                if self.get_value_named(child_iter, "name") is None:
                    return # already depopulated and placeholder in place
                while self.recursive_remove(child_iter):
                    pass
            self.insert_place_holder(dir_iter)
        def remove_place_holder(self, dir_iter):
            child_iter = self.iter_children(dir_iter)
            if child_iter and self.get_value_named(child_iter, "name") is None:
                self.remove(child_iter)
        def fs_path(self, fsobj_iter):
            if fsobj_iter is None:
                return None
            parent_iter = self.iter_parent(fsobj_iter)
            name = self.get_value_named(fsobj_iter, "name")
            if parent_iter is None:
                return name
            else:
                if name is None:
                    return os.path.join(self.fs_path(parent_iter), '')
                return os.path.join(self.fs_path(parent_iter), name)
        def _not_yet_populated(self, dir_iter):
            if self.iter_n_children(dir_iter) < 2:
                child_iter = self.iter_children(dir_iter)
                return child_iter is None or self.get_value_named(child_iter, "name") is None
            return False
        def on_row_expanded_cb(self, view, dir_iter, _dummy):
            if self._not_yet_populated(dir_iter):
                view._populate(self.fs_path(dir_iter), dir_iter)
                if self.iter_n_children(dir_iter) > 1:
                    self.remove_place_holder(dir_iter)
        def on_row_collapsed_cb(self, _view, dir_iter, _dummy):
            self.insert_place_holder_if_needed(dir_iter)
        def update_iter_row_tuple(self, fsobj_iter, to_tuple):
            for label in ["style", "foreground", "status", "related_file_str", "icon"]:
                self.set_value_named(fsobj_iter, label, getattr(to_tuple, label))
        def _get_file_paths(self, fsobj_iter, path_list):
            while fsobj_iter != None:
                if not self.get_value_named(fsobj_iter, "is_dir"):
                    path_list.append(self.fs_path(fsobj_iter))
                else:
                    child_iter = self.iter_children(fsobj_iter)
                    if child_iter != None:
                        self._get_file_paths(child_iter, path_list)
                fsobj_iter = self.iter_next(fsobj_iter)
        def get_file_paths(self):
            path_list = []
            self._get_file_paths(self.get_iter_first(), path_list)
            return path_list
    # This is not a method but a function within the FileTreeView namespace
    def _format_file_name_crcb(_column, cell_renderer, store, tree_iter, _arg=None):
        name = store.get_value_named(tree_iter, "name")
        if name is None:
            cell_renderer.set_property("text", _("<empty>"))
            return
        name += store.get_value_named(tree_iter, "related_file_str")
        cell_renderer.set_property("text", name)
    UI_DESCR = \
    '''
    <ui>
      <menubar name="files_menubar">
        <menu name="files_menu" action="menu_files">
         <menuitem action="refresh_files"/>
        </menu>
      </menubar>
      <popup name="files_popup">
          <menuitem action="modify_files_selection"/>
          <menuitem action="delete_files_selection"/>
          <menuitem action="new_file"/>
        <separator/>
          <menuitem action="copy_files_selection"/>
          <menuitem action="move_files_selection"/>
          <menuitem action="rename_file"/>
      </popup>
    </ui>
    '''
    specification = tlview.ViewSpec(
        properties={"headers-visible" : False},
        selection_mode=gtk.SELECTION_MULTIPLE,
        columns=[
            tlview.ColumnSpec(
                title=_("File Name"),
                properties={},
                cells=[
                    tlview.CellSpec(
                        cell_renderer_spec=tlview.CellRendererSpec(
                            cell_renderer=gtk.CellRendererPixbuf,
                            expand=False,
                            start=True
                        ),
                        properties={},
                        cell_data_function_spec=None,
                        attributes={"stock-id" : Model.col_index("icon")}
                    ),
                    tlview.CellSpec(
                        cell_renderer_spec=tlview.CellRendererSpec(
                            cell_renderer=gtk.CellRendererText,
                            expand=False,
                            start=True
                        ),
                        properties={},
                        cell_data_function_spec=None,
                        attributes={"text" : Model.col_index("status"), "style" : Model.col_index("style"), "foreground" : Model.col_index("foreground")}
                    ),
                    tlview.CellSpec(
                        cell_renderer_spec=tlview.CellRendererSpec(
                            cell_renderer=gtk.CellRendererText,
                            expand=False,
                            start=True
                        ),
                        properties={},
                        cell_data_function_spec=tlview.CellDataFunctionSpec(function=_format_file_name_crcb, user_data=None),
                        attributes={"style" : Model.col_index("style"), "foreground" : Model.col_index("foreground")}
                    )
                ]
            )
        ]
    )
    KEYVAL_c = gtk.gdk.keyval_from_name('c')
    KEYVAL_C = gtk.gdk.keyval_from_name('C')
    KEYVAL_ESCAPE = gtk.gdk.keyval_from_name('Escape')
    AUTO_EXPAND = False
    @staticmethod
    def _get_related_file_str(data):
        if data.related_file:
            if isinstance(data.related_file, str):
                return " <- " + data.related_file
            else:
                return " {0} {1}".format(data.related_file.relation, data.related_file.path)
        return ""
    @staticmethod
    def _handle_button_press_cb(widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS:
            if event.button == 2:
                widget.get_selection().unselect_all()
                return True
        return False
    @staticmethod
    def _handle_key_press_cb(widget, event):
        if event.state & gtk.gdk.CONTROL_MASK:
            if event.keyval in [FileTreeView.KEYVAL_c, FileTreeView.KEYVAL_C]:
                widget.add_selected_files_to_clipboard()
                return True
        elif event.keyval == FileTreeView.KEYVAL_ESCAPE:
            widget.get_selection().unselect_all()
            return True
        return False
    @staticmethod
    def search_equal_func(model, column, key, model_iter, _data=None):
        text = model.fs_path(model_iter)
        return text.find(key) == -1
    _FILE_ICON = {True : gtk.STOCK_DIRECTORY, False : gtk.STOCK_FILE}
    @classmethod
    def _generate_row_tuple(cls, data, isdir):
        deco = fsdb.Deco(pango.STYLE_NORMAL, "black")
        row = cls.Model.Row(
            name=data.name,
            is_dir=isdir,
            icon=cls._FILE_ICON[isdir],
            status=data.status,
            related_file_str=cls._get_related_file_str(data),
            style=deco.style,
            foreground=deco.foreground
        )
        return row
    def __init__(self, show_hidden=False, busy_indicator=None):
        dialogue.BusyIndicatorUser.__init__(self, busy_indicator=busy_indicator)
        self._file_db = fsdb.OsFileDb()
        ws_event.Listener.__init__(self)
        self.show_hidden_action = gtk.ToggleAction('show_hidden_files', _('Show Hidden Files'), _('Show/hide ignored files and those beginning with "."'), None)
        self.show_hidden_action.set_active(show_hidden)
        self.show_hidden_action.connect('toggled', self._toggle_show_hidden_cb)
        self.show_hidden_action.set_menu_item_type(gtk.CheckMenuItem)
        self.show_hidden_action.set_tool_item_type(gtk.ToggleToolButton)
        tlview.TreeView.__init__(self)
        self.set_search_equal_func(self.search_equal_func)
        ws_actions.AGandUIManager.__init__(self, selection=self.get_selection(), popup="/files_popup")
        self.connect("row-expanded", self.model.on_row_expanded_cb)
        self.connect("row-collapsed", self.model.on_row_collapsed_cb)
        self.connect("button_press_event", self._handle_button_press_cb)
        self.connect("key_press_event", self._handle_key_press_cb)
        self.get_selection().set_select_function(self._dirs_not_selectable, full=True)
        self.add_notification_cb(ws_event.AUTO_UPDATE, self.auto_update)
        self.add_notification_cb(ws_event.CHANGE_WD, self.repopulate)
        self.add_notification_cb(ws_event.FILE_CHANGES, self.update)
        # TODO: investigate whether repopulate() needs to be called here
        self.repopulate()
    def auto_update(self, _arg=None):
        if not self._file_db.is_current:
            self.update()
    def populate_action_groups(self):
        self.action_groups[actions.AC_DONT_CARE].add_action(self.show_hidden_action)
        self.action_groups[actions.AC_DONT_CARE].add_actions(
            [
                ('refresh_files', gtk.STOCK_REFRESH, _('_Refresh Files'), None,
                 _('Refresh/update the file tree display'), self.update),
            ])
        self.action_groups[ws_actions.AC_IN_TGND|actions.AC_SELN_MADE].add_actions(
            [
                ("modify_files_selection", gtk.STOCK_EDIT, _('_Modify'), None,
                 _('Modify the selected file(s)'), self.modify_selected_files_acb),
                ("copy_files_selection", gtk.STOCK_COPY, _('Copy'), None,
                 _('Copy the selected file(s)'), self.copy_selected_files_acb),
                ("move_files_selection", gtk.STOCK_PASTE, _('_Move/Rename'), None,
                 _('Move the selected file(s)'), self.move_selected_files_acb),
                ("delete_files_selection", gtk.STOCK_DELETE, _('_Delete'), None,
                 _('Delete the selected file(s)'), self.delete_selected_files_acb),
            ])
        self.action_groups[ws_actions.AC_IN_TGND|actions.AC_SELN_UNIQUE].add_actions(
           [
                ("rename_file", icons.STOCK_RENAME, _('Re_name/Move'), None,
                 _('Rename/move the selected file'), self.move_selected_files_acb),
            ])
        self.action_groups[ws_actions.AC_IN_TGND].add_actions(
            [
                ("new_file", gtk.STOCK_NEW, _('_New'), None,
                 _('Create a new file'), self.create_new_file_acb),
            ])
        self.action_groups[actions.AC_DONT_CARE].add_actions(
            [
                ("menu_files", None, _('_Files')),
            ])
    @property
    def _populate_all(self):
        return self.AUTO_EXPAND
    @property
    def show_hidden(self):
        return self.show_hidden_action.get_active()
    @show_hidden.setter
    def show_hidden(self, new_value):
        self.show_hidden_action.set_active(new_value)
        self._update_dir('', None)
    @staticmethod
    def _dirs_not_selectable(selection, model, path, is_selected, _arg=None):
        if not is_selected:
            return not model.get_value_named(model.get_iter(path), 'is_dir')
        return True
    def _toggle_show_hidden_cb(self, toggleaction):
        self.show_busy()
        self._update_dir('', None)
        self.unshow_busy()
    def _get_dir_contents(self, dirpath):
        return self._file_db.dir_contents(dirpath, show_hidden=self.show_hidden_action.get_active())
    def _row_expanded(self, dir_iter):
        return self.row_expanded(self.model.get_path(dir_iter))
    def _populate(self, dirpath, parent_iter):
        dirs, files = self._get_dir_contents(dirpath)
        for dirdata in dirs:
            row_tuple = self._generate_row_tuple(dirdata, True)
            dir_iter = self.model.append(parent_iter, row_tuple)
            if self._populate_all:
                self._populate(os.path.join(dirpath, dirdata.name), dir_iter)
                if self.AUTO_EXPAND:
                    self.expand_row(self.model.get_path(dir_iter), True)
            else:
                self.model.insert_place_holder(dir_iter)
        for filedata in files:
            row_tuple = self._generate_row_tuple(filedata, False)
            dummy = self.model.append(parent_iter, row_tuple)
        if parent_iter is not None:
            self.model.insert_place_holder_if_needed(parent_iter)
    def get_iter_for_filepath(self, filepath):
        pathparts = fsdb.split_path(filepath)
        child_iter = self.model.get_iter_first()
        for index in range(len(pathparts) - 1):
            while child_iter is not None:
                if self.model.get_value_named(child_iter, 'name') == pathparts[index]:
                    tpath = self.model.get_path(child_iter)
                    if not self.row_expanded(tpath):
                        self.expand_row(tpath, False)
                    child_iter = self.model.iter_children(child_iter)
                    break
                child_iter = self.model.iter_next(child_iter)
        while child_iter is not None:
            if self.model.get_value_named(child_iter, 'name') == pathparts[-1]:
                return child_iter
            child_iter = self.model.iter_next(child_iter)
        return None
    def select_filepaths(self, filepaths):
        seln = self.get_selection()
        seln.unselect_all()
        for filepath in filepaths:
            seln.select_iter(self.get_iter_for_filepath(filepath))
    def _update_dir(self, dirpath, parent_iter=None):
        changed = False
        if parent_iter is None:
            child_iter = self.model.get_iter_first()
        else:
            child_iter = self.model.iter_children(parent_iter)
            if child_iter:
                if self.model.get_value_named(child_iter, "name") is None:
                    child_iter = self.model.iter_next(child_iter)
        dirs, files = self._get_dir_contents(dirpath)
        dead_entries = []
        for dirdata in dirs:
            row_tuple = self._generate_row_tuple(dirdata, True)
            while (child_iter is not None) and self.model.get_value_named(child_iter, 'is_dir') and (self.model.get_value_named(child_iter, 'name') < dirdata.name):
                dead_entries.append(child_iter)
                child_iter = self.model.iter_next(child_iter)
            if child_iter is None:
                dir_iter = self.model.append(parent_iter, row_tuple)
                changed = True
                if self._populate_all:
                    self._update_dir(os.path.join(dirpath, dirdata.name), dir_iter)
                    if self.AUTO_EXPAND:
                        self.expand_row(self.model.get_path(dir_iter), True)
                else:
                    self.model.insert_place_holder(dir_iter)
                continue
            name = self.model.get_value_named(child_iter, "name")
            if (not self.model.get_value_named(child_iter, "is_dir")) or (name > dirdata.name):
                dir_iter = self.model.insert_before(parent_iter, child_iter, row_tuple)
                changed = True
                if self._populate_all:
                    self._update_dir(os.path.join(dirpath, dirdata.name), dir_iter)
                    if self.AUTO_EXPAND:
                        self.expand_row(self.model.get_path(dir_iter), True)
                else:
                    self.model.insert_place_holder(dir_iter)
                continue
            changed |= self.model.get_value_named(child_iter, "icon") != row_tuple.icon
            self.model.update_iter_row_tuple(child_iter, row_tuple)
            if self._populate_all or self._row_expanded(child_iter):
                changed |= self._update_dir(os.path.join(dirpath, name), child_iter)
            else:
                # make sure we don't leave bad data in children that were previously expanded
                self.model.depopulate(child_iter)
            child_iter = self.model.iter_next(child_iter)
        while (child_iter is not None) and self.model.get_value_named(child_iter, 'is_dir'):
            dead_entries.append(child_iter)
            child_iter = self.model.iter_next(child_iter)
        for filedata in files:
            row_tuple = self._generate_row_tuple(filedata, False)
            while (child_iter is not None) and (self.model.get_value_named(child_iter, 'name') < filedata.name):
                dead_entries.append(child_iter)
                child_iter = self.model.iter_next(child_iter)
            if child_iter is None:
                dummy = self.model.append(parent_iter, row_tuple)
                changed = True
                continue
            if self.model.get_value_named(child_iter, "name") > filedata.name:
                dummy = self.model.insert_before(parent_iter, child_iter, row_tuple)
                changed = True
                continue
            changed |= self.model.get_value_named(child_iter, "icon") != row_tuple.icon
            self.model.update_iter_row_tuple(child_iter, row_tuple)
            child_iter = self.model.iter_next(child_iter)
        while child_iter is not None:
            dead_entries.append(child_iter)
            child_iter = self.model.iter_next(child_iter)
        changed |= len(dead_entries) > 0
        for dead_entry in dead_entries:
            self.model.recursive_remove(dead_entry)
        if parent_iter is not None:
            self.model.insert_place_holder_if_needed(parent_iter)
        return changed
    @staticmethod
    def _get_file_db():
        return fsdb.OsFileDb()
    def repopulate(self, _arg=None):
        self.show_busy()
        self._file_db = self._get_file_db()
        self.model.clear()
        self._populate('', self.model.get_iter_first())
        self.unshow_busy()
    def update(self, _arg=None):
        self.show_busy()
        self._file_db = self._get_file_db()
        self._update_dir('', None)
        self.unshow_busy()
    def get_selected_filepaths(self, expanded=False):
        store, selection = self.get_selection().get_selected_rows()
        filepath_list = [store.fs_path(store.get_iter(x)) for x in selection]
        if expanded:
            return self.expand_filepaths(filepath_list)
        return filepath_list
    def add_selected_files_to_clipboard(self, clipboard=None):
        if not clipboard:
            clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        sel = utils.file_list_to_string(self.get_selected_filepaths())
        clipboard.set_text(sel)
    def get_filepaths_in_dir(self, dirname, show_hidden=True, recursive=True):
        # TODO: fix get_filepaths_in_dir() -- use db NOT view
        subdirs, files = self._file_db.dir_contents(dirname, show_hidden=show_hidden)
        filepaths = [os.path.join(dirname, fdata.name) for fdata in files]
        if recursive:
            for subdir in subdirs:
                filepaths += self.get_filepaths_in_dir(os.path.join(dirname, subdir.name), recursive)
        return filepaths
    def get_file_paths(self):
        return self.model.get_file_paths()
    def is_dir_filepath(self, filepath):
        return self.model.get_value_named(self.get_iter_for_filepath(filepath), "is_dir")
    def expand_filepaths(self, filepath_list, show_hidden=False, recursive=True):
        if isinstance(filepath_list, str):
            filepath_list = [filepath_list]
        expanded_list = []
        for filepath in filepath_list:
            if self.is_dir_filepath(filepath):
                expanded_list += self.get_filepaths_in_dir(filepath, show_hidden=show_hidden, recursive=recursive)
            else:
                expanded_list.append(filepath)
        return expanded_list
    def modify_selected_files_acb(self, _menu_item):
        dialogue.report_any_problems(ifce.modify_files(self.get_selected_filepaths(), gui_calling=True))
    def create_new_file(self, new_file_name, open_for_edit=False):
        self.show_busy()
        result = utils.create_file(new_file_name)
        self.unshow_busy()
        dialogue.report_any_problems(result)
        if open_for_edit:
            text_edit.edit_files_extern([new_file_name])
        return result
    def create_new_file_acb(self, _menu_item):
        dialog = gtk.FileChooserDialog(_('New File'), dialogue.main_window,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_position(gtk.WIN_POS_MOUSE)
        selected_files = self.get_selected_filepaths()
        if len(selected_files) == 1 and os.path.isdir(selected_files[0]):
            dialog.set_current_folder(os.path.abspath(selected_files[0]))
        else:
            dialog.set_current_folder(os.getcwd())
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            new_file_name = dialog.get_filename()
            dialog.destroy()
            self.create_new_file(new_file_name, False)
        else:
            dialog.destroy()
    def delete_files(self, file_list):
        if ifce.log:
            ifce.log.start_cmd(_('Deleting: {0}').format(utils.file_list_to_string(file_list)))
        serr = ""
        for filename in file_list:
            try:
                os.remove(filename)
                if ifce.log:
                    ifce.log.append_stdout(_('Deleted: {0}\n').format(filename))
            except os.error as value:
                errmsg = ("%s: %s" + os.linesep) % (value[1], filename)
                serr += errmsg
                if ifce.log:
                    ifce.log.append_stderr(errmsg)
        if ifce.log:
            ifce.log.end_cmd()
        ws_event.notify_events(ws_event.FILE_DEL)
        if serr:
            return cmd_result.Result(cmd_result.ERROR, "", serr)
        return cmd_result.Result(cmd_result.OK, "", "")
    def _delete_named_files(self, file_list, ask=True):
        if not ask or dialogue.confirm_list_action(file_list, _('About to be deleted. OK?')):
            self.show_busy()
            result = self.delete_files(file_list)
            self.unshow_busy()
            dialogue.report_any_problems(result)
    def delete_selected_files_acb(self, _menu_item):
        self._delete_named_files(self.get_selected_filepaths())
    def _get_target(self, src_file_list):
        if len(src_file_list) > 1:
            mode = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER
        else:
            mode = gtk.FILE_CHOOSER_ACTION_SAVE
        dialog = gtk.FileChooserDialog(_('Target'), dialogue.main_window, mode,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        if mode == gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER:
            dialog.set_current_folder(os.getcwd())
        else:
            dialog.set_current_folder(os.path.dirname(src_file_list[0]))
            dialog.set_current_name(os.path.basename(src_file_list[0]))
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            target = dialog.get_filename()
        else:
            target = None
        dialog.destroy()
        return (response, target)
    def _move_or_copy_files(self, file_list, operation, dry_run_first=True):
        response, target = self._get_target(file_list)
        if response == gtk.RESPONSE_OK:
            force = False
            is_ok = not dry_run_first
            if dry_run_first:
                self.show_busy()
                result = operation(file_list, target, force=False, dry_run=True)
                self.unshow_busy()
                if cmd_result.suggests_force(result):
                    is_ok = force = _check_if_force(result)
                    if not force:
                        return
                elif cmd_result.is_less_than_error(result):
                    lines = result.stdout.splitlines() + result.stderr.splitlines()
                    is_ok = not lines or dialogue.confirm_list_action(lines, _('About to be actioned. OK?'))
                else:
                    dialogue.report_any_problems(result)
                    return
            if is_ok:
                while True:
                    self.show_busy()
                    result = operation(file_list, target, force=force)
                    self.unshow_busy()
                    if not force and cmd_result.suggests_force(result):
                        force = _check_if_force(result)
                        if not force:
                            return
                        continue
                    break
                dialogue.report_any_problems(result)
    def copy_files(self, file_list, dry_run_first=True):
        self._move_or_copy_files(file_list, utils.os_copy_files, dry_run_first=dry_run_first)
    def copy_selected_files_acb(self, _action=None):
        self.copy_files(self.get_selected_filepaths())
    def move_files(self, file_list, dry_run_first=True):
        self._move_or_copy_files(file_list, utils.os_move_files, dry_run_first=dry_run_first)
    def move_selected_files_acb(self, _action=None):
        self.move_files(self.get_selected_filepaths())

class FileTreeWidget(gtk.VBox):
    MENUBAR = "/files_menubar"
    BUTTON_BAR_ACTIONS = ["show_hidden_files"]
    TREE_VIEW = FileTreeView
    SIZE = (240, 320)
    def __init__(self, busy_indicator=None, show_hidden=False, **kwargs):
        gtk.VBox.__init__(self)
        # file tree view wrapped in scrolled window
        self.file_tree = self.TREE_VIEW(busy_indicator=busy_indicator, show_hidden=show_hidden, **kwargs)
        scw = gtk.ScrolledWindow()
        scw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.file_tree.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.file_tree.set_headers_visible(False)
        self.file_tree.set_size_request(*self.SIZE)
        scw.add(self.file_tree)
        # file tree menu bar
        self.menu_bar = self.file_tree.ui_manager.get_widget(self.MENUBAR)
        self.pack_start(self.menu_bar, expand=False)
        self.pack_start(scw, expand=True, fill=True)
        # Mode selectors
        hbox = gtk.HBox()
        for action_name in self.BUTTON_BAR_ACTIONS:
            button = gtk.CheckButton()
            action = self.file_tree.action_groups.get_action(action_name)
            action.connect_proxy(button)
            gutils.set_widget_tooltip_text(button, action.get_property("tooltip"))
            hbox.pack_start(button)
        self.pack_start(hbox, expand=False)
        self.show_all()
