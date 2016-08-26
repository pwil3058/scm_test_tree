
import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from .. import config_data
from .. import utils
from .. import cmd_ifce
from .. import enotify

from . import ifce
from . import config
from . import dialogue
from . import actions
from . import ws_actions
from . import recollect
from . import icons
from . import file_tree_managed

class MainWindow(Gtk.Window, dialogue.BusyIndicator, actions.CAGandUIManager, enotify.Listener, ws_actions.WSListenerMixin):
    UI_DESCR = \
        '''
        <ui>
            <menubar name="left_side_menubar">
                <menu action="working_directory_menu">
                    <menuitem action="change_wd_action"/>
                    <menuitem action="new_tgnd_action"/>
                    <menuitem action="quit_action"/>
                </menu>
            </menubar>
            <menubar name="right_side_menubar">
                <menu action="configuration_menu">
                    <menuitem action="allocate_xtnl_editors"/>
                    <menuitem action="config_auto_update"/>
                </menu>
            </menubar>
        </ui>
        '''
    count = 0
    def __init__(self):
        assert MainWindow.count == 0
        MainWindow.count += 1
        Gtk.Window.__init__(self, Gtk.WindowType.TOPLEVEL)
        self.parse_geometry(recollect.get("main_window", "last_geometry"))
        self.set_icon_from_file(icons.APP_ICON_FILE)
        dialogue.BusyIndicator.__init__(self)
        self.connect("destroy", self._quit)
        dialogue.init(self)
        actions.CAGandUIManager.__init__(self)
        enotify.Listener.__init__(self)
        ws_actions.WSListenerMixin.__init__(self)
        self._lhs_menubar = self.ui_manager.get_widget("/left_side_menubar")
        self._lhs_menubar.insert(config.TestGroundsMenu(), 1)
        self._rhs_menubar = self.ui_manager.get_widget("/right_side_menubar")
        self._file_tree_widget = file_tree_managed.ManagedFileTreeWidget()
        # Now lay the widgets out
        vbox = Gtk.VBox()
        hbox = Gtk.HBox()
        hbox.pack_start(self._lhs_menubar, expand=True, fill=True, padding=0)
        hbox.pack_end(self._rhs_menubar, expand=False, fill=True, padding=0)
        vbox.pack_start(hbox, expand=False, fill=True, padding=0)
        if ifce.TERM:
            vpaned = Gtk.VPaned()
            vpaned.set_position(recollect.get("main_window", "vpaned_position"))
            vpaned.add1(self._file_tree_widget)
            vpaned.add2(ifce.TERM)
            vbox.pack_start(vpaned, expand=True, fill=True, padding=0)
        else:
            vbox.pack_start(self._file_tree_widget, expand=True, fill=True, padding=0)
        self.connect("configure_event", self._configure_event_cb)
        self.add(vbox)
        self.show_all()
        self._update_title()
        self.add_notification_cb(enotify.E_CHANGE_WD, self._reset_after_cd)
    def populate_action_groups(self):
        actions.CLASS_INDEP_AGS[actions.AC_DONT_CARE].add_actions(
            [
                ("working_directory_menu", None, _('_Working Directory')),
                ("configuration_menu", None, _('_Configuration')),
                ("change_wd_action", Gtk.STOCK_OPEN, _('_Open'), "",
                 _("Change current working directory"), self._change_wd_acb),
                ("new_tgnd_action", Gtk.STOCK_NEW, _('_New'), "",
                 _("Create a new test ground and change workspace to that directory"), self._new_tgnd_acb),
                ("quit_action", Gtk.STOCK_QUIT, _("_Quit"), "",
                 _("Quit"), self._quit),
            ])
    def _quit(self, _widget):
        Gtk.main_quit()
    def _update_title(self):
        self.set_title(config_data.APP_NAME + ": {0}".format(utils.path_rel_home(os.getcwd())))
    def _reset_after_cd(self, *args, **kwargs):
        self.show_busy()
        self._update_title()
        self.unshow_busy()
    def _change_wd_acb(self, _action=None):
        open_dialog = config.WSOpenDialog(parent=self)
        if open_dialog.run() == Gtk.ResponseType.OK:
            wspath = open_dialog.get_path()
            if wspath:
                open_dialog.show_busy()
                result = ifce.chdir(wspath)
                open_dialog.unshow_busy()
                dialogue.report_any_problems(result)
        open_dialog.destroy()
    def _new_tgnd_acb(self, _action):
        dirname = dialogue.ask_dir_name(_("{0}: Browse for Directory").format(config_data.APP_NAME), existing=True, parent=self)
        if dirname:
            result = cmd_ifce.create_test_tree(dirname, gui_calling=True)
            if result.is_less_than_error:
                ifce.chdir(dirname)
            dialogue.report_any_problems(result)
    def _configure_event_cb(self, widget, event):
        recollect.set("main_window", "last_geometry", "{0.width}x{0.height}+{0.x}+{0.y}".format(event))
    def _paned_notify_cb(self, widget, parameter, oname=None):
        if parameter.name == "position":
            recollect.set("main_window", oname, str(widget.get_position()))
