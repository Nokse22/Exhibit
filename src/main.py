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
import webbrowser

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw, GLib
from .window import Viewer3dWindow

class Viewer3dApplication(Adw.Application):
    """The main application singleton class."""

    open_filepath = None

    def __init__(self):
        super().__init__(application_id='io.github.nokse22.Exhibit',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)

        GLib.setenv("GDK_DEBUG", "gl-prefer-gl", True)
        GLib.setenv("GSK_RENDERER", "gl", True)
        GLib.setenv("GDK_DEBUG", "gl-egl", True)

        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)

        self.create_action('open-hdri-folder', self.on_open_hdri_folder)

        self.create_action('open-new-window', self.open_new_window_action, ['<primary><shift>n'])
        self.create_action('toggle-orthographic', self.toggle_orthographic, ['<primary>5'])
        self.create_action('front-view', self.front_view, ['<primary>1'])
        self.create_action('right-view', self.right_view, ['<primary>3'])
        self.create_action('top-view', self.top_view, ['<primary>7'])
        self.create_action('isometric-view', self.isometric_view, ['<primary>9'])

        self.create_action('move-camera-w', self.on_move_camera, ['<primary>w'], "w")
        self.create_action('move-camera-a', self.on_move_camera, ['<primary>a'], "a")
        self.create_action('move-camera-s', self.on_move_camera, ['<primary>s'], "s")
        self.create_action('move-camera-d', self.on_move_camera, ['<primary>d'], "d")

        self.create_action('rotate-camera-left', self.on_rotate_camera, ['<primary>Left'], "left")
        self.create_action('rotate-camera-right', self.on_rotate_camera, ['<primary>Right'], "right")
        self.create_action('rotate-camera-up', self.on_rotate_camera, ['<primary>Up'], "up")
        self.create_action('rotate-camera-down', self.on_rotate_camera, ['<primary>Down'], "down")

        user_home_dir = os.environ.get("XDG_CONFIG_HOME", os.environ["HOME"])
        show_image_external_action = Gio.SimpleAction.new_stateful(
                'show-image-externally',
                GLib.VariantType.new("s"),
                GLib.Variant("s", user_home_dir))
        show_image_external_action.connect('activate', self.show_image_external)
        self.add_action(show_image_external_action)

        self.saved_settings = Gio.Settings.new('io.github.nokse22.Exhibit')

        theme_action = Gio.SimpleAction.new_stateful(
            "theme",
            GLib.VariantType.new("s"),
            GLib.Variant("s", self.saved_settings.get_string("theme")),
        )
        theme_action.connect("activate", self.on_theme_setting_changed)

        self.update_theme()

        self.add_action(theme_action)

    def do_open(self, files, n_files, hint):
        for file in files:
            file_path = file.get_path()
            win = Viewer3dWindow(application=self, startup_filepath=file_path)
            win.present()

    def show_image_external(self, _action, image_path: GLib.Variant, *args):
        try:
            image_file = Gio.File.new_for_path(image_path.get_string())
        except GLib.GError as e:
            print("Failed to construct a new Gio.File object from path.")
        else:
            launcher = Gtk.FileLauncher.new(image_file)

            def open_image_finish(_, result, *args):
                try:
                    launcher.launch_finish(result)
                except GLib.GError as e:
                    if e.code != 2: # 'The portal dialog was dismissed by the user' error
                        print("Failed to finish Gtk.FileLauncher procedure.")

            launcher.launch(self.props.active_window, None, open_image_finish)

    def on_about_action(self, *args):
        about = Adw.AboutDialog(
                                application_name='Exhibit',
                                application_icon='io.github.nokse22.Exhibit',
                                developer_name='Nokse22',
                                version='1.2.0',
                                website='https://github.com/Nokse22/Exhibit',
                                issue_url='https://github.com/Nokse22/Exhibit/issues',
                                developers=['Nokse'],
                                license_type="GTK_LICENSE_GPL_3_0",
                                copyright='© 2024 Nokse22',
                                artists=["Jakub Steiner https://jimmac.eu"])
        about.add_link(_("Checkout F3D"), "https://f3d.app")
        about.present(self.props.active_window)

    def on_open_hdri_folder(self, *args):
        webbrowser.open(self.props.active_window.hdri_path)

    def on_theme_setting_changed(self, action: Gio.SimpleAction, state: GLib.Variant):
        action.set_state(state)
        self.saved_settings.set_string("theme", state.get_string())
        self.update_theme()

    def on_move_camera(self, action, _, direction):
        match direction:
            case "w":
                self.props.active_window.f3d_viewer.pan(0, 0, 1)
            case "a":
                self.props.active_window.f3d_viewer.pan(-1, 0, 0)
            case "s":
                self.props.active_window.f3d_viewer.pan(0, 0, -1)
            case "d":
                self.props.active_window.f3d_viewer.pan(1, 0, 0)

    def on_rotate_camera(self, action, _, direction):
        self.props.active_window.f3d_viewer.rotate_camera(direction)

    def update_theme(self):
        manager  = Adw.StyleManager().get_default()
        match self.saved_settings.get_string("theme"):
            case "follow":
                manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
            case "light":
                manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            case "dark":
                manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

    def toggle_orthographic(self, *args):
        self.props.active_window.toggle_orthographic()

    def front_view(self, *args):
        self.props.active_window.f3d_viewer.front_view()

    def right_view(self, *args):
        self.props.active_window.f3d_viewer.right_view()

    def top_view(self, *args):
        self.props.active_window.f3d_viewer.top_view()

    def isometric_view(self, *args):
        self.props.active_window.f3d_viewer.isometric_view()

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            if self.open_filepath:
                win = Viewer3dWindow(application=self, startup_filepath=self.open_filepath)
            else:
                win = Viewer3dWindow(application=self)
        win.present()

    def open_new_window_action(self, *args):
        win = Viewer3dWindow(application=self)
        win.present()

    def create_action(self, name, callback, shortcuts=None, argument=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        if argument:
            action.connect("activate", callback, argument)
        else:
            action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

def main(version):
    """The application's entry point."""
    app = Viewer3dApplication()
    return app.run(sys.argv)

