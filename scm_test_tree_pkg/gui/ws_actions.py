### Copyright (C) 2005 Peter Williams <pwil3058@gmail.com>

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

'''
Workspace status action groups
'''

import collections

import gtk

from . import ifce
from . import actions
from . import ws_event

AC_NOT_IN_TGND, AC_IN_TGND, AC_IN_TGND_MASK = actions.ActionCondns.new_flags_and_mask(2)

def get_in_tgnd_condns():
    return actions.MaskedCondns(AC_IN_TGND if ifce.in_valid_test_gnd else AC_NOT_IN_TGND, AC_IN_TGND_MASK)

def _update_class_indep_cwd_cb(_arg=None):
    actions.CLASS_INDEP_AGS.update_condns(get_in_tgnd_condns())

ws_event.add_notification_cb(ifce.E_CHANGE_WD, _update_class_indep_cwd_cb)

class AGandUIManager(actions.CAGandUIManager, ws_event.Listener):
    def __init__(self, selection=None, popup=None):
        actions.CAGandUIManager.__init__(self, selection=selection, popup=popup)
        ws_event.Listener.__init__(self)
        self.add_notification_cb(ifce.E_CHANGE_WD, self.cwd_condns_change_cb)
        self.init_action_states()
    def cwd_condns_change_cb(self, _arg=None):
        self.action_groups.update_condns(get_in_tgnd_condns())
    def init_action_states(self):
        self.action_groups.update_condns(get_in_tgnd_condns())

actions.CLASS_INDEP_AGS[actions.AC_DONT_CARE].add_actions(
    [
        ("actions_wd_menu", None, _('_Working Directory')),
        ("actions_quit", gtk.STOCK_QUIT, _('_Quit'), "",
         _('Quit'), gtk.main_quit),
    ])
