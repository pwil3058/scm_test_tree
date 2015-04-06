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

def _ui_manager_connect_proxy(_ui_mgr, action, widget):
    tooltip = action.get_property('tooltip')
    if isinstance(widget, gtk.MenuItem) and tooltip:
        widget.set_tooltip_text(tooltip)

class UIManager(gtk.UIManager):
    def __init__(self):
        gtk.UIManager.__init__(self)
        self.connect('connect-proxy', _ui_manager_connect_proxy)
