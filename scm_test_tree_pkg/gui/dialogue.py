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

import os

import gtk

from . import cmd_result
from . import config_data

from . import gutils

main_window = None

def show_busy():
    if main_window is not None:
        main_window.show_busy()

def unshow_busy():
    if main_window is not None:
        main_window.unshow_busy()

def is_busy():
    return main_window is None or main_window.is_busy

def init(window):
    global main_window
    main_window = window

class BusyIndicator:
    def __init__(self, parent=None):
        self.parent_indicator = parent
        self._count = 0
    def show_busy(self):
        if self.parent:
            self.parent.show_busy()
        self._count += 1
        if self._count == 1 and self.window:
            self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            while gtk.events_pending():
                gtk.main_iteration()
    def unshow_busy(self):
        if self.parent:
            self.parent.unshow_busy()
        self._count -= 1
        assert self._count >= 0
        if self._count == 0 and self.window:
            self.window.set_cursor(None)
    @property
    def is_busy(self):
        return self._count > 0

class BusyIndicatorUser:
    def __init__(self, busy_indicator=None):
        self._busy_indicator = busy_indicator
    def show_busy(self):
        if self._busy_indicator is not None:
            self._busy_indicator.show_busy()
        else:
            show_busy()
    def unshow_busy(self):
        if self._busy_indicator is not None:
            self._busy_indicator.unshow_busy()
        else:
            unshow_busy()
    def set_busy_indicator(self, busy_indicator=None):
        self._busy_indicator = busy_indicator

class Dialog(gtk.Dialog, BusyIndicator):
    def __init__(self, title=None, parent=None, flags=0, buttons=None):
        if not parent:
            parent = main_window
        gtk.Dialog.__init__(self, title=title, parent=parent, flags=flags, buttons=buttons)
        if not parent:
            self.set_icon_from_file(icons.APP_ICON_FILE)
        BusyIndicator.__init__(self)
    def report_any_problems(self, result):
        report_any_problems(result, self)
    def inform_user(self, msg):
        inform_user(msg, parent=self)
    def warn_user(self, msg):
        warn_user(msg, parent=self)
    def alert_user(self, msg):
        alert_user(msg, parent=self)

class MessageDialog(gtk.MessageDialog):
    def __init__(self, parent=None, flags=0, type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_NONE, message_format=None):
        if not parent:
            parent = main_window
        gtk.MessageDialog.__init__(self, parent=parent, flags=flags, type=type, buttons=buttons, message_format=message_format)

class FileChooserDialog(gtk.FileChooserDialog):
    def __init__(self, title=None, parent=None, action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=None, backend=None):
        if not parent:
            parent = main_window
        gtk.FileChooserDialog.__init__(self, title=title, parent=parent, action=action, buttons=buttons, backend=backend)

class QuestionDialog(Dialog):
    def __init__(self, title=None, parent=None, flags=0, buttons=None, question=""):
        Dialog.__init__(self, title=title, parent=parent, flags=flags, buttons=buttons)
        hbox = gtk.HBox()
        self.vbox.add(hbox)
        hbox.show()
        self.image = gtk.Image()
        self.image.set_from_stock(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_DIALOG)
        hbox.pack_start(self.image, expand=False)
        self.image.show()
        self.tview = gtk.TextView()
        self.tview.set_cursor_visible(False)
        self.tview.set_editable(False)
        self.tview.set_size_request(320, 80)
        self.tview.show()
        self.tview.get_buffer().set_text(question)
        hbox.add(gutils.wrap_in_scrolled_window(self.tview))
    def set_question(self, question):
        self.tview.get_buffer().set_text(question)

def ask_question(question, parent=None,
                 buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                          gtk.STOCK_OK, gtk.RESPONSE_OK)):
    dialog = QuestionDialog(parent=parent,
                            flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                            buttons=buttons, question=question)
    response = dialog.run()
    dialog.destroy()
    return response

def ask_ok_cancel(question, parent=None):
    return ask_question(question, parent) == gtk.RESPONSE_OK

def confirm_list_action(alist, question, parent=None):
    return ask_ok_cancel('\n'.join(alist + ['\n', question]), parent)

class Response(object):
    SKIP = 1
    SKIP_ALL = 2
    FORCE = 3
    REFRESH = 4
    RECOVER = 5
    RENAME = 6
    DISCARD = 7
    EDIT = 8
    MERGE = 9
    OVERWRITE = 10

def _form_question(result, clarification):
    if clarification:
        return '\n'.join(list(result[1:]) + [clarification])
    else:
        return '\n'.join(result[1:])

def ask_force_or_cancel(result, clarification=None, parent=None):
    buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, _('_Force'), Response.FORCE)
    question = _form_question(result, clarification)
    return ask_question(question, parent, buttons)

def ask_dir_name(prompt, suggestion=None, existing=True, parent=None):
    if existing:
        mode = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER
        if suggestion and not os.path.exists(suggestion):
            suggestion = None
    else:
        mode = gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER
    dialog = FileChooserDialog(prompt, parent, mode,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OK, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)
    if suggestion:
        if os.path.isdir(suggestion):
            dialog.set_current_folder(suggestion)
        else:
            dirname = os.path.dirname(suggestion)
            if dirname:
                dialog.set_current_folder(dirname)
    response = dialog.run()
    if response == gtk.RESPONSE_OK:
        new_dir_name = os.path.relpath(dialog.get_filename())
    else:
        new_dir_name = None
    dialog.destroy()
    return new_dir_name

def inform_user(msg, parent=None, problem_type=gtk.MESSAGE_INFO):
    dialog = MessageDialog(parent=parent,
                           flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                           type=problem_type, buttons=gtk.BUTTONS_CLOSE,
                           message_format=msg)
    dialog.run()
    dialog.destroy()

def report_any_problems(result, parent=None):
    if cmd_result.is_ok(result):
        return
    elif cmd_result.is_warning(result):
        problem_type = gtk.MESSAGE_WARNING
    else:
        problem_type = gtk.MESSAGE_ERROR
    inform_user(os.linesep.join(result[1:]), parent, problem_type)

def report_failure(failure, parent=None):
    result = failure.result
    if result.ecode != 0:
        inform_user(os.linesep.join(result[1:]), parent, gtk.MESSAGE_ERROR)

def report_exception(exc_data, parent=None):
    import traceback
    msg = ''.join(traceback.format_exception(exc_data[0], exc_data[1], exc_data[2]))
    dialog = MessageDialog(parent=parent,
                           flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                           type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_CLOSE,
                           message_format=config_data.get_report_request_msg())
    dialog.set_title(_(config_data.APP_NAME + ": Unexpected Exception"))
    dialog.format_secondary_text(msg)
    dialog.run()
    dialog.destroy()
