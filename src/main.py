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

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import Viewer3dWindow
from .preferences import Preferences


class Viewer3dApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='io.github.nokse22.Exhibit',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)
        self.create_action('play-animation', self.on_play_animation, ['space'])
        self.create_action('save-as-image', self.on_save_as_image_action, ['<primary>s'])
        self.create_action('toggle-grid', self.on_toggle_grid_action, ['<primary>g'])

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        self.win = self.props.active_window
        if not self.win:
            self.win = Viewer3dWindow(application=self)
        self.win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
                                application_name='Exhibit',
                                application_icon='io.github.nokse22.Exhibit',
                                developer_name='Nokse22',
                                version='0.1.0',
                                website='https://github.com/Nokse22/Exhibit',
                                issue_url='https://github.com/Nokse22/Exhibit/issues',
                                developers=['Nokse22'],
                                copyright='© 2024 Nokse22')

        about.present(self.win)

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""

        preferences = Preferences()

        preferences.translucency_switch.set_active(self.win.settings.get_boolean("translucency"))
        preferences.grid_switch.set_active(self.win.settings.get_boolean("grid"))
        preferences.tone_mapping_switch.set_active(self.win.settings.get_boolean("tone-mapping"))
        preferences.ambient_occlusion_switch.set_active(self.win.settings.get_boolean("ambient-occlusion"))
        preferences.anti_aliasing_switch.set_active(self.win.settings.get_boolean("anti-aliasing"))
        preferences.hdri_ambient_switch.set_active(self.win.settings.get_boolean("hdri-ambient"))
        preferences.point_up_switch.set_active(self.win.settings.get_boolean("point-up"))

        preferences.light_intensity_spin.set_value(self.win.settings.get_boolean("hdri-ambient"))

        preferences.translucency_switch.connect("notify::active", self.win.on_switch_toggled, "translucency")
        preferences.grid_switch.connect("notify::active", self.win.on_switch_toggled, "grid")
        preferences.tone_mapping_switch.connect("notify::active", self.win.on_switch_toggled, "tone-mapping")
        preferences.ambient_occlusion_switch.connect("notify::active", self.win.on_switch_toggled, "ambient-occlusion")
        preferences.anti_aliasing_switch.connect("notify::active", self.win.on_switch_toggled, "anti-aliasing")
        preferences.hdri_ambient_switch.connect("notify::active", self.win.on_switch_toggled, "hdri-ambient")

        preferences.point_up_switch.connect("notify::active", self.win.set_point_up)

        preferences.light_intensity_spin.connect("notify::value", self.win.on_spin_changed, "light-intensity")

        preferences.present()

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

    def on_play_animation(self, *args):
        pass

    def on_save_as_image_action(self, *args):
        self.win.open_save_file_chooser()

    def on_toggle_grid_action(self, *args):
        self.win.toggle_grid()

def main(version):
    """The application's entry point."""
    app = Viewer3dApplication()
    return app.run(sys.argv)
