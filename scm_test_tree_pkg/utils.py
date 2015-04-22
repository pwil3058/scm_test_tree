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
import shutil

from . import fsdb
from . import cmd_result
from . import ws_event
from . import urlops

HOME = os.path.expanduser("~")

def path_rel_home(path):
    """Return the given path as a path relative to user's home directory."""
    if urlops.parse_url(path).scheme:
        return path
    path = os.path.abspath(path)
    len_home = len(HOME)
    if len(path) >= len_home and HOME == path[:len_home]:
        path = "~" + path[len_home:]
    return path

# handle the fact os.path.samefile is not available on all operating systems
def samefile(filename1, filename2):
    """Return whether the given paths refer to the same file or not."""
    try:
        return os.path.samefile(filename1, filename2)
    except AttributeError:
        return os.path.abspath(filename1) == os.path.abspath(filename2)

def create_file(name, console=None):
    """Attempt to create a file with the given name and report the outcome as
    a cmd_result tuple.
    1. If console is not None print report of successful creation on it.
    2. If a file with same name already exists fail and report a warning.
    3. If file creation fails for other reasons report an error.
    """
    if not os.path.exists(name):
        try:
            if console:
                console.start_cmd('create "%s"' % name)
            open(name, 'w').close()
            if console:
                console.end_cmd()
            ws_event.notify_events(ws_event.FILE_ADD)
            return cmd_result.Result(cmd_result.OK, '', '')
        except (IOError, OSError) as msg:
            return cmd_result.Result(cmd_result.ERROR, '', '"%s": %s' % (name, msg))
    else:
        return cmd_result.Result(cmd_result.WARNING, '', _('"%s": file already exists') % name)

def os_move_or_copy_file(file_path, dest, opsym, force=False, dry_run=False, extra_checks=None, verbose=False):
    assert opsym in (fsdb.Relation.MOVED_TO, fsdb.Relation.COPIED_TO), _("Invalid operation requested")
    if os.path.isdir(dest):
        dest = os.path.join(dest, os.path.basename(file_path))
    omsg = "{0} {1} {2}.".format(file_path, opsym, dest) if verbose else ""
    if dry_run:
        if os.path.exists(dest):
            return cmd_result.Result(cmd_result.ERROR_SUGGEST_FORCE, omsg, _('File "{0}" already exists. Select "force" to overwrite.').format(dest))
        else:
            return cmd_result.Result(cmd_result.OK, omsg, "")
    if not force and os.path.exists(dest):
        emsg = _('File "{0}" already exists. Select "force" to overwrite.').format(dest)
        result = cmd_result.Result(cmd_result.ERROR_SUGGEST_FORCE, omsg, emsg)
        return result
    if extra_checks:
        result = extra_check([(file_path, dest)])
        if result.ecode is not cmd_result.OK:
            return result
    try:
        if opsym is fsdb.Relation.MOVED_TO:
            os.rename(file_path, dest)
        elif opsym is fsdb.Relation.COPIED_TO:
            shutil.copy(file_path, dest)
        result = cmd_result.Result(cmd_result.OK, omsg, "")
    except (IOError, os.error, shutil.Error) as why:
        result = cmd_result.Result(cmd_result.ERROR, omsg, _('"{0}" {1} "{2}" failed. {3}.\n') % (file_path, opsym, dest, str(why)))
    ws_event.notify_events(ws_event.FILE_ADD|ws_event.FILE_DEL)
    return result

def os_move_or_copy_files(file_path_list, dest, opsym, force=False, dry_run=False, extra_checks=None, verbose=False):
    assert opsym in (fsdb.Relation.MOVED_TO, fsdb.Relation.COPIED_TO), _("Invalid operation requested")
    def _overwrite_msg(overwrites):
        if len(overwrites) == 0:
            return ""
        elif len(overwrites) > 1:
            return _("Files:\n\t{0}\nalready exist. Select \"force\" to overwrite.").format("\n\t".join(["\"" + fp + "\"" for fp in overwrites]))
        else:
            return _("File \"{0}\" already exists. Select \"force\" to overwrite.").format(overwrites[0])
    if len(file_path_list) == 1:
        return os_move_or_copy_file(file_path_list[0], dest, opsym, force=force, dry_run=dry_run, extra_checks=extra_checks)
    if not os.path.isdir(dest):
        result = cmd_result.Result(cmd_result.ERROR, '', _('"{0}": Destination must be a directory for multifile rename.').format(dest))
        return result
    opn_paths_list = [(file_path, os.path.join(dest, os.path.basename(file_path))) for file_path in file_path_list]
    omsg = "\n".join(["{0} {1} {2}.".format(src, opsym, dest) for (src, dest) in opn_paths_list]) if verbose else ""
    if dry_run:
        overwrites = [dest for (src, dest) in opn_paths_list if os.path.exists(dest)]
        if len(overwrites) > 0:
            emsg = _overwrite_msg(overwrites)
            return cmd_result.Result(cmd_result.ERROR_SUGGEST_FORCE, omsg, emsg)
        else:
            return cmd_result.Result(cmd_result.OK, omsg, "")
    if not force:
        overwrites = [dest for (src, dest) in opn_paths_list if os.path.exists(dest)]
        if len(overwrites) > 0:
            emsg = _overwrite_msg(overwrites)
            result = cmd_result.Result(cmd_result.ERROR_SUGGEST_FORCE, omsg, emsg)
            return result
    if extra_checks:
        result = extra_check(opn_paths_list)
        if result.ecode is not cmd_result.OK:
            return result
    failed_opns_str = ""
    for (src, dest) in opn_paths_list:
        try:
            if opsym is fsdb.Relation.MOVED_TO:
                os.rename(src, dest)
            elif opsym is fsdb.Relation.COPIED_TO:
                if os.path.isdir(src):
                    shutil.copytree(src, dest)
                else:
                    shutil.copy2(src, dest)
        except (IOError, os.error, shutil.Error) as why:
            serr = _('"{0}" {1} "{2}" failed. {3}.\n').format(src, opsym, dest, str(why))
            failed_opns_str += serr
            continue
    ws_event.notify_events(ws_event.FILE_ADD|ws_event.FILE_DEL)
    if failed_opns_str:
        return cmd_result.Result(cmd_result.ERROR, omsg, failed_opns_str)
    return cmd_result.Result(cmd_result.OK, omsg, "")

def os_copy_file(file_path, dest, force=False, dry_run=False):
    return os_move_or_copy_file(file_path, dest, opsym=fsdb.Relation.COPIED_TO, force=force, dry_run=dry_run)

def os_copy_files(file_path_list, dest, force=False, dry_run=False):
    return os_move_or_copy_files(file_path_list, dest, opsym=fsdb.Relation.COPIED_TO, force=force, dry_run=dry_run)

def os_move_file(file_path, dest, force=False, dry_run=False):
    return os_move_or_copy_file(file_path, dest, opsym=fsdb.Relation.MOVED_TO, force=force, dry_run=dry_run)

def os_move_files(file_path_list, dest, force=False, dry_run=False):
    return os_move_or_copy_files(file_path_list, dest, opsym=fsdb.Relation.MOVED_TO, force=force, dry_run=dry_run)
