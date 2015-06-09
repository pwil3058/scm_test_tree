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

import sys
import collections
import os
import datetime

COUNT_FILE = ".scmtt_modify_count"

def create_test_tree(base_dir_name="", gui_calling=False):
    '''Execute the "create" sub command using the supplied args'''
    if gui_calling:
        from . import cmd_result
    if base_dir_name:
        if not os.path.exists(base_dir_name):
            try:
                os.makedirs(base_dir_name)
            except os.error as edata:
                emsg = "{0}: {1}".format(edata.filename, edata.strerror)
                return cmd_result.Result(cmd_result.ERROR, "", emsg) if gui_calling else emsg
        elif not os.path.isdir(base_dir_name):
            emsg = _("{0}: is NOT a directory. Aborting.").format(base_dir_name)
            return cmd_result.Result(cmd_result.ERROR, "", emsg) if gui_calling else emsg
    # Do this here to catch base directory permission problems early
    try:
        open(os.path.join(base_dir_name, COUNT_FILE), 'w').write("0")
    except IOError as edata:
        emsg = "{0}: {1}".format(edata.filename, edata.strerror)
        return cmd_result.Result(cmd_result.ERROR, "", emsg) if gui_calling else emsg
    combined_emsgs = ""
    for dindex in range(6):
        if dindex:
            dname = 'dir{0}'.format(dindex)
            try:
                os.mkdir(os.path.join(base_dir_name, dname))
            except OSError as edata:
                emsg = "{0}: {1}\n".format(edata.filename, edata.strerror)
                if gui_calling:
                    combined_emsgs += emsg
                else:
                    sys.stderr.write(emsg)
        else:
            dname = ""
        print dindex, dname
        for sdindex in range(6):
            if sdindex:
                if not dindex:
                    continue
                sdname = 'subdir{0}'.format(sdindex)
                try:
                    os.mkdir(os.path.join(base_dir_name, dname, sdname))
                except OSError as edata:
                    emsg = "{0}: {1}\n".format(edata.filename, edata.strerror)
                    if gui_calling:
                        combined_emsgs += emsg
                    else:
                        sys.stderr.write(emsg)
            else:
                sdname = ''
            print sdindex, sdname
            for findex in range(1, 6):
                print findex
                for (fn_template, c_template) in [("file{0}", _("{0}: is a text file.\n")), ("binary{0}", _("{0}:\000is a binary file.\n")), (".hidden{0}", _("{0}:is a hidden file.\n"))]:
                    fpath = os.path.join(dname, sdname, fn_template.format(findex))
                    try:
                        open(os.path.join(base_dir_name, fpath), 'w').write(c_template.format(fpath))
                    except IOError as edata:
                        emsg = "{0}: {1}\n".format(edata.filename, edata.strerror)
                        if gui_calling:
                            combined_emsgs += emsg
                        else:
                            sys.stderr.write(emsg)
    if gui_calling:
        return cmd_result.Result(cmd_result.WARNING if combined_emsgs else cmd_result.OK, "", combined_emsgs)
    return 0

def modify_files(filepath_list, add_tws=False, no_newline=False, gui_calling=False):
    '''Execute the "modify" sub command using the supplied args'''
    if gui_calling:
        from . import cmd_result
    try:
        modno = int(open(COUNT_FILE, 'r').read()) + 1
        open(COUNT_FILE, 'w').write("{0}".format(modno))
    except IOError:
        emsg = _('{0}: is NOT a valid test directory. Aborting.\n').format(os.getcwd())
        if gui_calling:
            return cmd_result.Result(cmd_result.ERROR, "", emsg)
        else:
            return emsg
    template = 'tws \ntws\t\n' if add_tws else ''
    template += 'Path: "{{0}}" modification #{0} at: {1}'.format(modno, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
    template += '' if no_newline else '\n'
    if not filepath_list:
        pass # TODO: generate list of all files in dir (except scm databases)
    combined_emsgs = ""
    for filepath in filepath_list:
        if filepath == COUNT_FILE:
            continue
        elif not os.path.exists(filepath):
            emsg = '{0}: file does not exist.  Ignored.\n'.format(filepath)
            if gui_calling:
                combined_emsgs += emsg
            else:
                sys.stderr.write(emsg)
            continue
        elif os.path.isdir(filepath):
            emsg = '{0}: is a directory ignored.  Ignored.\n'.format(filepath)
            if gui_calling:
                combined_emsgs += emsg
            else:
                sys.stderr.write(emsg)
            continue
        try:
            with open(filepath, 'ab') as fobj:
                fobj.write(template.format(filepath))
        except IOError as edata:
            emsg = "{0}: {1}\n".format(edata.filename, edata.strerror)
            if gui_calling:
                combined_emsgs += emsg
            else:
                sys.stderr.write(emsg)
    if gui_calling:
        return cmd_result.Result(cmd_result.WARNING if combined_emsgs else cmd_result.OK, "", combined_emsgs)
    return 0

in_valid_test_gnd = False

TERM = None
log = False

def get_test_tree_root(fdir=None):
    if not fdir:
        fdir = os.getcwd()
    root = fdir
    while True:
        cf_path = os.path.join(root, COUNT_FILE)
        if os.path.exists(cf_path) and not os.path.isdir(cf_path):
            return root
        newroot = os.path.dirname(root)
        if root == newroot:
            break
        root = newroot
    return None

def init(start_dir=None):
    from . import cmd_result
    from . import config_data
    from .gui import terminal
    from .gui import ws_event
    from .gui import recollect
    global TERM
    global in_valid_test_gnd
    if terminal.AVAILABLE:
        TERM = terminal.Terminal()
    base_dir = get_test_tree_root(start_dir)
    if base_dir is not None:
        from .gui import config
        os.chdir(base_dir)
        TERM.set_cwd(base_dir)
        config.TGndPathTable.append_saved_wd(base_dir)
        in_valid_test_gnd = True
        recollect.set(config_data.APP_NAME, "last_wd", base_dir)
    else:
        in_valid_test_gnd = False
    ws_event.notify_events(ws_event.CHANGE_WD)
    return cmd_result.Result(cmd_result.OK, "", "")

def close():
    from . import cmd_result
    return cmd_result.Result(cmd_result.OK, "", "")

def chdir(newdir=None):
    from . import cmd_result
    from . import config_data
    from . import utils
    from .gui import terminal
    from .gui import ws_event
    from .gui import recollect
    global in_valid_test_gnd
    old_wd = os.getcwd()
    retval = cmd_result.Result(cmd_result.OK, "", "")
    if newdir:
        try:
            os.chdir(newdir)
        except OSError as err:
            import errno
            ecode = errno.errorcode[err.errno]
            emsg = err.strerror
            retval = cmd_result.Result(cmd_result.ERROR, "", '%s: "%s" :%s' % (ecode, newdir, emsg))
    base_dir = get_test_tree_root()
    if base_dir is not None:
        from . import config
        os.chdir(base_dir)
        TERM.set_cwd(base_dir)
        config.TGndPathTable.append_saved_wd(base_dir)
        in_valid_test_gnd = True
        recollect.set(config_data.APP_NAME, "last_wd", base_dir)
    else:
        in_valid_test_gnd = False
    new_wd = os.getcwd()
    if not utils.samefile(new_wd, old_wd):
        if TERM:
            TERM.set_cwd(new_wd)
    ws_event.notify_events(ws_event.CHANGE_WD)
    return retval
