# main.py
#
# Copyright 2024 Nokse22
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import gi
import os

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import Viewer3dWindow

class Viewer3dApplication(Adw.Application):
    """The main application singleton class."""

    open_filepath = None

    def __init__(self):
        super().__init__(application_id='io.github.nokse22.Exhibit',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('open-new-window', self.open_new_window_action, ['<primary><shift>n'])

        # self.connect("open", self.on_open)

    def on_open(self, window, files, *args):
        for file in files:
            file_path = file.get_path()
            if file_path:
                if not os.path.exists(file_path):
                    self.open_filepath = file_path
        self.do_activate()

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            if self.open_filepath:
                win = Viewer3dWindow(application=self, filepath=self.open_filepath)
            else:
                win = Viewer3dWindow(application=self)
        win.present()

    def open_new_window_action(self, *args):
        self.win = Viewer3dWindow(application=self)
        self.win.present()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

def main(version):
    """The application's entry point."""
    app = Viewer3dApplication()
    return app.run(sys.argv)
