# window.py
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

import gi
from gi.repository import Adw
from gi.repository import Gtk, Gdk, Gio, GLib

import f3d
from f3d import *

import math
import os

from OpenGL.GL import *

@Gtk.Template(resource_path='/io/github/nokse22/Exhibit/window.ui')
class Viewer3dWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'Viewer3dWindow'

    gl_area = Gtk.Template.Child()

    title_widget = Gtk.Template.Child()
    open_button = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    view_button_headerbar = Gtk.Template.Child()

    keys = {
    "grid": "render.grid.enable",
    "translucency": "render.effect.translucency-support",
    "tone-mapping":"render.effect.tone-mapping",
    "ambient-occlusion": "render.effect.ambient-occlusion",
    "anti-aliasing" :"render.effect.anti-aliasing",
    "hdri-ambient" :"render.hdri.ambient",
    "background-skybox": "render.background.skybox",
    "background-blur": "background.blur",
    "light-intensity": "render.light.intensity",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_css_class("devel")

        self.settings = Gio.Settings.new('io.github.nokse22.Exhibit')

        # self.settings.on_bool_setting_changed("changed", self.on_setting_changed)

        self.options = {
            "scene.up-direction": "+Y",
            "render.background.color": [1.0, 1.0, 1.0],
            "render.grid.enable": self.settings.get_boolean("grid"),
            "render.effect.translucency-support": self.settings.get_boolean("translucency"),
            "render.effect.tone-mapping": self.settings.get_boolean("tone-mapping"),
            "render.effect.ambient-occlusion": self.settings.get_boolean("ambient-occlusion"),
            "render.effect.anti-aliasing": self.settings.get_boolean("anti-aliasing"),
            "render.hdri.ambient": self.settings.get_boolean("hdri-ambient"),
        }

        self.engine = Engine(Window.EXTERNAL)
        self.loader = self.engine.getLoader()
        self.camera = self.engine.window.getCamera()

        self.engine.autoload_plugins()

        self.camera.setFocalPoint((0,0,0))

        if self.settings.get_boolean("orthographic"):
            self.toggle_orthographic()

        inital_options = {
            "scene.up-direction": "+Y",
            "render.background.color": [1.0, 1.0, 1.0],
        }

        self.engine.options.update(inital_options)

        self.gl_area.set_auto_render(True)
        self.gl_area.connect("realize", self.on_realize)
        self.gl_area.connect("render", self.on_render)

        self.gl_area.set_allowed_apis(Gdk.GLAPI.GL)
        # self.gl_area.set_required_version(1, 0)

        self.prev_pan_offset = 0
        self.drag_prev_offset = (0, 0)
        self.drag_start_angle = 0

        self.point_up = True

        self.style_manager = Adw.StyleManager()
        self.style_manager.connect("notify::dark", self.update_theme)

    def update_theme(self, *args):
        if self.style_manager.get_dark():
            options = {"render.background.color": [0.2, 0.2, 0.2]}
        else:
            options = {"render.background.color": [1.0, 1.0, 1.0]}
        self.engine.options.update(options)
        self.gl_area.queue_render()

    def on_realize(self, area):
        self.gl_area.get_context().make_current()

    def on_render(self, area, ctx):
        self.gl_area.get_context().make_current()
        self.engine.window.render()

        return True

    @Gtk.Template.Callback("on_scroll")
    def on_scroll(self, gesture, dx, dy):
        if (dy == -1.0):
            self.camera.dolly(1.1)
        elif (dy == 1.0):
            self.camera.dolly(0.9)

        self.gl_area.queue_render()

    @Gtk.Template.Callback("on_drag_update")
    def on_drag_update(self, gesture, x_offset, y_offset):
        self.camera.elevation(-(self.drag_prev_offset[1] - y_offset))
        self.camera.azimuth(self.drag_prev_offset[0] - x_offset)

        if self.point_up:
            self.camera.setViewUp((0.0, 1.0, 0.0))

        self.gl_area.queue_render()

        self.drag_prev_offset = (x_offset, y_offset)

    @Gtk.Template.Callback("on_drag_end")
    def on_drag_end(self, gesture, *args):
        self.drag_prev_offset = (0, 0)

    def open_file_chooser(self):
        dialog = Gtk.FileDialog(
            title=_("Open File"),
        )
        dialog.open(self, None, self.on_open_file_response)

    def on_open_file_response(self, dialog, response):
        file = dialog.open_finish(response)

        if file:
            filepath = file.get_path()
            self.engine.loader.load_scene(filepath)

            self.camera.resetToBounds()
            self.camera.setCurrentAsDefault()

            file_name = os.path.basename(filepath)

            self.title_widget.set_subtitle(file_name)
            self.stack.set_visible_child_name("3d_page")

            GLib.timeout_add(200, self.update_options)

    def update_options(self):
        self.engine.options.update(self.options)
        self.update_theme()
        self.gl_area.queue_render()

        return False

    def save_as_image(self, filepath):
        self.gl_area.get_context().make_current()
        img = self.engine.window.render_to_image()
        img.save(filepath)

    def open_save_file_chooser(self):
        dialog = Gtk.FileDialog(
            title=_("Save File"),
            initial_name=_("image.png"),
        )
        dialog.save(self, None, self.on_save_file_response)

    def on_save_file_response(self, dialog, response):
        try:
            file = dialog.save_finish(response)
        except:
            return

        if file:
            file_path = file.get_path()
            self.save_as_image(file_path)

    @Gtk.Template.Callback("on_home_clicked")
    def on_home_clicked(self, btn):
        self.camera.resetToDefault()
        self.gl_area.queue_render()

    @Gtk.Template.Callback("on_open_button_clicked")
    def on_open_button_clicked(self, btn):
        self.open_file_chooser()

    @Gtk.Template.Callback("on_view_clicked")
    def toggle_orthographic(self, *args):
        btn = self.view_button_headerbar
        if (btn.get_icon_name() == "perspective-symbolic"):
            btn.set_icon_name("orthographic-symbolic")
            camera_options = {"scene.camera.orthographic": True}
            self.settings.set_boolean("orthographic", True)
        else:
            btn.set_icon_name("perspective-symbolic")
            camera_options = {"scene.camera.orthographic": False}
            self.settings.set_boolean("orthographic", False)
        self.engine.options.update(camera_options)
        self.gl_area.queue_render()

    def on_switch_toggled(self, switch, active, name):
        options = {self.keys[name]: switch.get_active()}
        self.settings.set_boolean(name, switch.get_active())
        self.engine.options.update(options)
        self.gl_area.queue_render()

    def on_spin_changed(self, spin, value, name):
        options = {self.keys[name]: spin.get_value()}
        self.settings.set_double(name, spin.get_value())
        self.engine.options.update(options)
        self.gl_area.queue_render()

    def set_point_up(self, switch, active):
        val = switch.get_active()
        self.point_up = val
        if val:
            self.camera.setViewUp((0.0, 1.0, 0.0))
            self.gl_area.queue_render()
