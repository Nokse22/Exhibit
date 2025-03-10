# main.py
#
# Copyright 2024-2025 Nokse <nokse@posteo.com>
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
import os
import webbrowser
import f3d

from gi.repository import Gtk, Gio, Adw, GLib
from .window import Viewer3dWindow

from gettext import gettext as _

from . import logger_lib


class Viewer3dApplication(Adw.Application):
    """The main application singleton class."""

    open_filepath = None

    def __init__(self):
        super().__init__(application_id='io.github.nokse22.Exhibit',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)

        logger_lib.init()

        self.lib_info = f3d.Engine.get_lib_info()
        self.backends = f3d.Engine.get_rendering_backend_list()

        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('help', self.on_help_action, ['F1'])

        self.create_action('open-hdri-folder', self.on_open_hdri_folder)
        self.create_action('open-configs-folder', self.on_open_configs_folder)

        self.create_action(
            'open-externally',
            lambda *_: self.props.active_window.on_open_externally(),
            ['<primary>O'])

        self.create_action(
            'open-new-window',
            self.open_new_window_action, ['<primary><shift>n'])
        self.create_action(
            'toggle-orthographic', self.toggle_orthographic, ['<primary>5'])
        self.create_action('front-view', self.front_view, ['<primary>1'])
        self.create_action('right-view', self.right_view, ['<primary>3'])
        self.create_action('top-view', self.top_view, ['<primary>7'])
        self.create_action(
            'isometric-view', self.isometric_view, ['<primary>9'])

        self.create_action(
            'move-camera-w', self.on_move_camera, ['<primary>w'], "w")
        self.create_action(
            'move-camera-a', self.on_move_camera, ['<primary>a'], "a")
        self.create_action(
            'move-camera-s', self.on_move_camera, ['<primary>s'], "s")
        self.create_action(
            'move-camera-d', self.on_move_camera, ['<primary>d'], "d")

        self.create_action(
            'rotate-camera-left',
            self.on_rotate_camera, ['<primary>Left'], "left")
        self.create_action(
            'rotate-camera-right',
            self.on_rotate_camera, ['<primary>Right'], "right")
        self.create_action(
            'rotate-camera-up',
            self.on_rotate_camera, ['<primary>Up'], "up")
        self.create_action(
            'rotate-camera-down',
            self.on_rotate_camera, ['<primary>Down'], "down")

        user_home_dir = os.environ.get("XDG_CONFIG_HOME", os.environ["HOME"])
        show_image_external_action = Gio.SimpleAction.new_stateful(
                'show-image-externally',
                GLib.VariantType.new("s"),
                GLib.Variant("s", user_home_dir))
        show_image_external_action.connect(
            'activate', self.show_image_external)
        self.add_action(show_image_external_action)

        self.saved_settings = Gio.Settings.new('io.github.nokse22.Exhibit')

        theme_action = Gio.SimpleAction.new_stateful(
            "theme",
            GLib.VariantType.new("s"),
            GLib.Variant("s", self.saved_settings.get_string("theme")))
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
        except Exception as e:
            self.logger.error(e)
        else:
            launcher = Gtk.FileLauncher.new(image_file)

            def open_image_finish(_, result, *args):
                try:
                    launcher.launch_finish(result)
                except Exception as e:
                    self.logger.error(e)

            launcher.launch(self.props.active_window, None, open_image_finish)

    def on_about_action(self, *args):
        about = Adw.AboutDialog(
            application_name='Exhibit',
            application_icon='io.github.nokse22.Exhibit',
            developer_name='Nokse',
            version='1.5.0',
            website='https://github.com/Nokse22/Exhibit',
            issue_url='https://github.com/Nokse22/Exhibit/issues',
            developers=['Nokse'],
            license_type="GTK_LICENSE_GPL_3_0",
            copyright='© 2024-2025 Nokse',
            artists=["Jakub Steiner https://jimmac.eu"])
        about.add_link(_("Checkout F3D"), "https://f3d.app")

        about.set_debug_info(
            f"GDK_DEBUG: {GLib.getenv('GDK_DEBUG')}\n" +
            f"GSK_RENDERER: {GLib.getenv('GSK_RENDERER')}\n" +
            f"DISPLAY: {GLib.getenv('DISPLAY')}\n" +
            f"XDG_SESSION_TYPE: {GLib.getenv('XDG_SESSION_TYPE')}\n" +
            f"XDG_SESSION_DESKTOP: {GLib.getenv('XDG_SESSION_DESKTOP')}\n" +
            f"GTK_THEME: {GLib.getenv('GTK_THEME')}\n" +
            f"GTK Version: {Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION}.{Gtk.MICRO_VERSION}\n" +
            "\n" +
            f"F3D Version: {self.lib_info.version_full}\n" +
            f"Build Date: {self.lib_info.build_date}\n" +
            f"Build System: {self.lib_info.build_system}\n" +
            f"VTK Version: {self.lib_info.vtk_version}\n" +
            f"F3D License: {self.lib_info.license}\n" +
            "\n" +
            f"Modules:\n{'\n'.join([f'- {key}: {val}' for key, val in self.lib_info.modules.items()])}\n" +
            f"Backends:\n{'\n'.join([f'- {key}: {val}' for key, val in self.backends.items()])}" +
            f"\nF3D Copyrights:\n- {'\n- '.join(self.lib_info.copyrights)}\n"
        )

        about.present(self.props.active_window)

    def on_help_action(self, *args):
        Gio.AppInfo.launch_default_for_uri("help:exhibit")

    def on_open_hdri_folder(self, *args):
        webbrowser.open(self.props.active_window.hdri_path)

    def on_open_configs_folder(self, *args):
        webbrowser.open(self.props.active_window.user_configurations_path)

    def on_theme_setting_changed(self, action, state):
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
        manager = Adw.StyleManager().get_default()
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
        win = self.props.active_window
        if not win:
            if self.open_filepath:
                win = Viewer3dWindow(
                    application=self, startup_filepath=self.open_filepath)
            else:
                win = Viewer3dWindow(application=self)
        win.present()

    def open_new_window_action(self, *args):
        win = Viewer3dWindow(application=self)
        win.present()

    def create_action(self, name, callback, shortcuts=None, argument=None):
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
