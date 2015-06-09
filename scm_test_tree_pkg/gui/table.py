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

"""
Provide generic enhancements to Textview widgets primarily to create
them from templates and allow easier access to named contents.
"""

import gtk

from . import gutils
from . import actions
from . import ws_actions
from . import ws_event
from . import tlview
from . import icons
from . import dialogue

ALWAYS_ON = 'table_always_on'
MODIFIED = 'table_modified'
NOT_MODIFIED = 'table_not_modified'
SELECTION = 'table_selection'
NO_SELECTION = 'table_no_selection'
UNIQUE_SELECTION = 'table_unique_selection'

TABLE_STATES = \
    [ALWAYS_ON, MODIFIED, NOT_MODIFIED, SELECTION, NO_SELECTION,
     UNIQUE_SELECTION]

# TODO: modify this code to use the new actions model
class Table(gtk.VBox):
    View = tlview.ListView
    def __init__(self, size_req=None):
        gtk.VBox.__init__(self)
        self.view = self.View()
        self.seln = self.view.get_selection()
        if size_req:
            self.view.set_size_request(*size_req)
        self.pack_start(gutils.wrap_in_scrolled_window(self.view))
        self.action_groups = {}
        for key in TABLE_STATES:
            self.action_groups[key] = gtk.ActionGroup(key)
        self.action_groups[ALWAYS_ON].add_actions(
            [
                ('table_add_row', gtk.STOCK_ADD, _('_Add'), None,
                 _('Add a new entry to the table'), self._add_row_acb),
            ])
        self.action_groups[MODIFIED].add_actions(
            [
                ('table_undo_changes', gtk.STOCK_UNDO, _('_Undo'), None,
                 _('Undo unapplied changes'), self._undo_changes_acb),
                ('table_apply_changes', gtk.STOCK_APPLY, _('_Apply'), None,
                 _('Apply outstanding changes'), self._apply_changes_acb),
            ])
        self.action_groups[SELECTION].add_actions(
            [
                ('table_delete_selection', gtk.STOCK_DELETE, _('_Delete'), None,
                 _('Delete selected row(s)'), self._delete_selection_acb),
                ('table_insert_row', icons.STOCK_INSERT, _('_Insert'), None,
                 _('Insert a new entry before the selected row(s)'), self._insert_row_acb),
            ])
        self._modified = False
        self.model.connect('row-inserted', self._row_inserted_cb)
        self.seln.connect('changed', self._selection_changed_cb)
        self.view.register_modification_callback(self._set_modified, True)
        self.seln.unselect_all()
        self._selection_changed_cb(self.seln)
    @property
    def model(self):
        return self.view.get_model()
    def _set_modified(self, val):
        self._modified = val
        self.action_groups[MODIFIED].set_sensitive(val)
        self.action_groups[NOT_MODIFIED].set_sensitive(not val)
    def _fetch_contents(self):
        assert False, _("Must be defined in child")
    def set_contents(self):
        self.model.set_contents(self._fetch_contents())
        self._set_modified(False)
    def get_contents(self):
        return [row for row in self.model.named()]
    def apply_changes(self):
        assert False, _("Must be defined in child")
    def _row_inserted_cb(self, model, path, model_iter):
        self._set_modified(True)
    def _selection_changed_cb(self, selection):
        rows = selection.count_selected_rows()
        self.action_groups[SELECTION].set_sensitive(rows > 0)
        self.action_groups[NO_SELECTION].set_sensitive(rows == 0)
        self.action_groups[UNIQUE_SELECTION].set_sensitive(rows == 1)
    def _undo_changes_acb(self, _action=None):
        self.set_contents()
    def _apply_changes_acb(self, _action=None):
        self.apply_changes()
    def _add_row_acb(self, _action=None):
        model_iter = self.model.append(None)
        self.view.get_selection().select_iter(model_iter)
        return
    def _delete_selection_acb(self, _action=None):
        model, paths = self.seln.get_selected_rows()
        iters = []
        for path in paths:
            iters.append(model.get_iter(path))
        for model_iter in iters:
            model.remove(model_iter)
    def _insert_row_acb(self, _action=None):
        model, paths = self.seln.get_selected_rows()
        if not paths:
            return
        model_iter = self.model.insert_before(model.get_iter(paths[0]), None)
        self.view.get_selection().select_iter(model_iter)
        return
    def get_selected_data(self, columns=None):
        store, selected_rows = self.seln.get_selected_rows()
        if not columns:
            columns = list(range(store.get_n_columns()))
        result = []
        for row in selected_rows:
            model_iter = store.get_iter(row)
            assert model_iter is not None
            result.append(store.get(model_iter, *columns))
        return result
    def get_selected_data_by_label(self, labels):
        columns = self.model.col_indices(labels)
        return self.get_selected_data(columns)
