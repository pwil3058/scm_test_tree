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

import collections

import gtk
import gobject

def pygtk_version_ge(version):
    for index in range(len(version)):
        if gtk.pygtk_version[index] >  version[index]:
            return True
        elif gtk.pygtk_version[index] <  version[index]:
            return False
    return True

if pygtk_version_ge((2, 12)):
    def set_widget_tooltip_text(widget, text):
        widget.set_tooltip_text(text)
else:
    tooltips = gtk.Tooltips()
    tooltips.enable()

    def set_widget_tooltip_text(widget, text):
        tooltips.set_tip(widget, text)

def wrap_in_scrolled_window(widget, policy=(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC), with_frame=True, label=None):
    scrw = gtk.ScrolledWindow()
    scrw.set_policy(policy[0], policy[1])
    scrw.add(widget)
    if with_frame:
        frame = gtk.Frame(label)
        frame.add(scrw)
        frame.show_all()
        return frame
    else:
        scrw.show_all()
        return scrw

class MutableComboBoxEntry(gtk.ComboBoxEntry):
    def __init__(self, entries=None):
        self.saved_text = ''
        gtk.ComboBoxEntry.__init__(self, gtk.ListStore(str))
        self.entry_set = set()
        for entry in entries if entries else []:
            if entry not in self.entry_set:
                self.append_text(entry)
                self.entry_set.add(entry)
        self.set_active(-1)
        self.child.connect('changed', self.changed_cb)
    def changed_cb(self, entry):
        if self.get_active() == -1:
            self.saved_text = entry.get_text()
        else:
            text = self.saved_text.rstrip()
            # no duplicates, empty strings or strings starting with white space
            if text and text[0] not in [' ', '\t'] and text not in self.entry_set:
                self.entry_set.add(text)
                self.prepend_text(text)
            self.saved_text = ''
        return
    def get_text(self):
        return self.child.get_text()
    def set_text(self, text):
        text = text.rstrip()
        if text and text[0] not in [' ', '\t'] and text not in self.entry_set:
            self.prepend_text(text)
            self.set_active(0)
            self.entry_set.add(text)
        else:
            self.child.set_text(text)

class TimeOutController():
    ToggleData = collections.namedtuple('ToggleData', ['name', 'label', 'tooltip', 'stock_id'])
    def __init__(self, toggle_data, function=None, is_on=True, interval=10000):
        self._interval = abs(interval)
        self._timeout_id = None
        self._function = function
        self.toggle_action = gtk.ToggleAction(
                toggle_data.name, toggle_data.label,
                toggle_data.tooltip, toggle_data.stock_id
            )
        self.toggle_action.set_menu_item_type(gtk.CheckMenuItem)
        self.toggle_action.set_tool_item_type(gtk.ToggleToolButton)
        self.toggle_action.connect("toggled", self._toggle_acb)
        self.toggle_action.set_active(is_on)
        self._toggle_acb()
    def _toggle_acb(self, _action=None):
        if self.toggle_action.get_active():
            self._timeout_id = gobject.timeout_add(self._interval, self._timeout_cb)
    def _timeout_cb(self):
        if self._function:
            self._function()
        return self.toggle_action.get_active()
    def stop_cycle(self):
        if self._timeout_id:
            gobject.source_remove(self._timeout_id)
            self._timeout_id = None
    def restart_cycle(self):
        self.stop_cycle()
        self._toggle_acb()
    def set_function(self, function):
        self.stop_cycle()
        self._function = function
        self._toggle_acb()
    def set_interval(self, interval):
        if interval > 0 and interval != self._interval:
            self._interval = interval
            self.restart_cycle()
    def get_interval(self):
        return self._interval
    def set_active(self, active=True):
        if active != self.toggle_action.get_active():
            self.toggle_action.set_active(active)
        self.restart_cycle()

TOC_DEFAULT_REFRESH_TD = TimeOutController.ToggleData("auto_refresh_toggle", _('Auto _Refresh'), _('Turn data auto refresh on/off'), gtk.STOCK_REFRESH)

class RefreshController(TimeOutController):
    def __init__(self, toggle_data=None, function=None, is_on=True, interval=10000):
        if toggle_data is None:
            toggle_data = TOC_DEFAULT_REFRESH_TD
        TimeOutController.__init__(self, toggle_data, function=function, is_on=is_on, interval=interval)

TOC_DEFAULT_SAVE_TD = TimeOutController.ToggleData("auto_save_toggle", _('Auto _Save'), _('Turn data auto save on/off'), gtk.STOCK_SAVE)

def _ui_manager_connect_proxy(_ui_mgr, action, widget):
    tooltip = action.get_property('tooltip')
    if isinstance(widget, gtk.MenuItem) and tooltip:
        widget.set_tooltip_text(tooltip)

class UIManager(gtk.UIManager):
    def __init__(self):
        gtk.UIManager.__init__(self)
        self.connect('connect-proxy', _ui_manager_connect_proxy)
