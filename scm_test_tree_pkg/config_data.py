### Copyright (C) 2013 Peter Williams <pwil3058@gmail.com>
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

import os
import gettext

HOME = os.path.expanduser("~")

from . import APP_NAME
from . import ISSUES_URL

CONFIG_DIR_NAME = os.sep.join([HOME, "." + APP_NAME + ".d"])

if not os.path.exists(CONFIG_DIR_NAME):
    os.mkdir(CONFIG_DIR_NAME, 0o775)

def get_report_request_msg():
    return \
    _("""
    Please report this problem by raising an issue at:
      {}
    and including a copy of the details below this message.

    Thank you.
    """).format(ISSUES_URL)
