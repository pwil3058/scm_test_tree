
import os

import gtk

from scm_test_tree_pkg import config_data
from scm_test_tree_pkg import config
from scm_test_tree_pkg import utils
from scm_test_tree_pkg import ifce
from scm_test_tree_pkg import dialogue
from scm_test_tree_pkg import actions
from scm_test_tree_pkg import ws_actions
from scm_test_tree_pkg import ws_event
from scm_test_tree_pkg import recollect
from scm_test_tree_pkg import icons
from scm_test_tree_pkg import file_tree

class MainWindow(gtk.Window, dialogue.BusyIndicator, ws_actions.AGandUIManager):
    UI_DESCR = \
        '''
        <ui>
            <menubar name="left_side_menubar">
                <menu action="working_directory_menu">
                    <menuitem action="change_wd_action"/>
                    <menuitem action="quit_action"/>
                </menu>
            </menubar>
            <menubar name="right_side_menubar">
                <menu action="configuration_menu">
                    <menuitem action="config_auto_update"/>
                </menu>
            </menubar>
        </ui>
        '''
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
        self._lhs_menubar = self.ui_manager.get_widget("/left_side_menubar")
        self._lhs_menubar.insert(config.TestGroundsMenu(), 1)
        self._rhs_menubar = self.ui_manager.get_widget("/right_side_menubar")
        self._file_tree_widget = file_tree.FileTreeWidget()
        # Now lay the widgets out
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        hbox.pack_start(self._lhs_menubar, expand=True)
        hbox.pack_end(self._rhs_menubar, expand=False)
        vbox.pack_start(hbox, expand=False)
        if ifce.TERM:
            vpaned = gtk.VPaned()
            vpaned.set_position(recollect.get("main_window", "vpaned_position"))
            vpaned.add1(self._file_tree_widget)
            vpaned.add2(ifce.TERM)
            vbox.pack_start(vpaned, expand=True)
        else:
            vbox.pack_start(self._file_tree_widget, expand=True)
        self.connect("configure_event", self._configure_event_cb)
        self.add(vbox)
        self.show_all()
        self._update_title()
        self.add_notification_cb(ws_event.CHANGE_WD, self._reset_after_cd)
    def populate_action_groups(self):
        actions.CLASS_INDEP_AGS[actions.AC_DONT_CARE].add_actions(
            [
                ("working_directory_menu", None, _('_Working Directory')),
                ("configuration_menu", None, _('_Configuration')),
                ("change_wd_action", gtk.STOCK_OPEN, _('_Open'), "",
                 _('Change current working directory'), self._change_wd_acb),
                ("quit_action", gtk.STOCK_QUIT, _('_Quit'), "",
                 _('Quit'), self._quit),
            ])
    def _quit(self, _widget):
        gtk.main_quit()
    def _update_title(self):
        self.set_title(config_data.APP_NAME + ": {0}".format(utils.path_rel_home(os.getcwd())))
    def _reset_after_cd(self, _arg=None):
        self.show_busy()
        self._update_title()
        self.unshow_busy()
    def _change_wd_acb(self, _action=None):
        open_dialog = config.WSOpenDialog(parent=self)
        if open_dialog.run() == gtk.RESPONSE_OK:
            wspath = open_dialog.get_path()
            if wspath:
                open_dialog.show_busy()
                result = ifce.chdir(wspath)
                open_dialog.unshow_busy()
                dialogue.report_any_problems(result)
        open_dialog.destroy()
    def _configure_event_cb(self, widget, event):
        recollect.set("main_window", "last_geometry", "{0.width}x{0.height}+{0.x}+{0.y}".format(event))
    def _paned_notify_cb(self, widget, parameter, oname=None):
        if parameter.name == "position":
            recollect.set("main_window", oname, str(widget.get_position()))
