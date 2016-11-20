### Copyright (C) 2007-2015 Peter Williams <pwil3058@gmail.com>
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

# A dummy console facilitate code sharing in othe modules

from .bab.decorators import singleton

@singleton
class ConsoleLogWidget(object):
    def start_cmd(self, cmd):
        return
    def append_stdin(self, msg):
        return
    def append_stdout(self, msg):
        return
    def append_stderr(self, msg):
        return
    def end_cmd(self, result=None):
        return
    def append_entry(self, msg):
        return

LOG = ConsoleLogWidget()
