### Copyright (C) 2015 Peter Williams <peter_ono@users.sourceforge.net>
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

def create_test_tree(base_dir_name=""):
    '''Execute the "create" sub command using the supplied args'''
    if base_dir_name:
        if not os.path.exists(base_dir_name):
            try:
                os.makedirs(base_dir_name)
            except os.error as edata:
                sys.exit(edata)
        elif not os.path.isdir(base_dir_name):
            sys.exit(_("{0}: is NOT a directory. Aborting.").format(base_dir_name))
    for dindex in range(6):
        if dindex:
            dname = 'dir{0}'.format(dindex)
            os.mkdir(os.path.join(base_dir_name, dname))
        else:
            dname = ""
        for sdindex in range(6):
            if sdindex:
                if not dindex:
                    continue
                sdname = 'subdir{0}'.format(sdindex)
                os.mkdir(os.path.join(base_dir_name, dname, sdname))
            else:
                sdname = ''
            for findex in range(1, 6):
                tfpath = os.path.join(dname, sdname, 'file{0}'.format(findex))
                open(os.path.join(base_dir_name, tfpath), 'w').write('{0}: is a text file.\n'.format(tfpath))
                bfpath = os.path.join(dname, sdname, 'binary{0}'.format(findex))
                open(os.path.join(base_dir_name, bfpath), 'w').write('{0}:\000is a binary file.\n'.format(bfpath))
                hfpath = os.path.join(dname, sdname, '.hidden{0}'.format(findex))
                open(os.path.join(base_dir_name, hfpath), 'w').write('{0}:is a hidden file.\n'.format(hfpath))
    open(os.path.join(base_dir_name, COUNT_FILE), 'w').write("0")
    return 0

def modify_files(filepath_list, add_tws=False, no_newline=False):
    '''Execute the "modify" sub command using the supplied args'''
    try:
        modno = int(open(COUNT_FILE, 'r').read()) + 1
        open(COUNT_FILE, 'w').write("{0}".format(modno))
    except IOError:
        sys.exit(_('{0}: is NOT a valid test directory. Aborting.\n').format(os.getcwd()))
    template = 'tws \ntws\t\n' if add_tws else ''
    template += 'Path: "{{0}}" modification #{0} at: {1}'.format(modno, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
    template += '' if no_newline else '\n'
    if not filepath_list:
        pass # TODO: generate list of all files in dir (except scm databases)
    for filepath in filepath_list:
        if filepath == COUNT_FILE:
            continue
        elif not os.path.exists(filepath):
            sys.stderr.write('{0}: file does not exist.  Ignored.\n'.format(filepath))
            continue
        elif os.path.isdir(filepath):
            sys.stderr.write('{0}: is a directory ignored.  Ignored.\n'.format(filepath))
            continue
        with open(filepath, 'ab') as fobj:
            fobj.write(template.format(filepath))
    return 0
