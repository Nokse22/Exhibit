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

# from OpenGL.GL import *

from .preferences import Preferences

class WindowSettings():
    def __init__(self):
        super().__init__()

        self.saved_settings = Gio.Settings.new('io.github.nokse22.Exhibit')

        self.settings = {
            "grid": self.saved_settings.get_boolean("grid"),
            "translucency": self.saved_settings.get_boolean("translucency"),
            "tone-mapping": self.saved_settings.get_boolean("tone-mapping"),
            "ambient-occlusion": self.saved_settings.get_boolean("ambient-occlusion"),
            "anti-aliasing": self.saved_settings.get_boolean("anti-aliasing"),
            "hdri-ambient": self.saved_settings.get_boolean("hdri-ambient"),
            "light-intensity": self.saved_settings.get_double("light-intensity"),
            "orthographic": self.saved_settings.get_boolean("orthographic"),
            "point-up": self.saved_settings.get_boolean("point-up"),
        }

    def set_setting(self, key, val):
        self.settings[key] = val

    def get_setting(self, key):
        return self.settings[key]

    def save_all_settings(self):
        self.saved_settings.set_boolean("grid", self.settings["grid"])
        self.saved_settings.set_boolean("translucency", self.settings["translucency"])
        self.saved_settings.set_boolean("tone-mapping", self.settings["tone-mapping"])
        self.saved_settings.set_boolean("ambient-occlusion", self.settings["ambient-occlusion"])
        self.saved_settings.set_boolean("anti-aliasing", self.settings["anti-aliasing"])
        self.saved_settings.set_boolean("hdri-ambient", self.settings["hdri-ambient"])
        self.saved_settings.set_double("light-intensity", self.settings["light-intensity"])
        self.saved_settings.set_boolean("orthographic", self.settings["orthographic"])
        self.saved_settings.set_boolean("point-up", self.settings["point-up"])

        print("settings saved")

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
        "orthographic": "scene.camera.orthographic",
    }

    up_dirs = {
        0: "-X",
        1: "+X",
        2: "-Y",
        3: "+Y",
        4: "-Z",
        5: "+Z"
    }

    def __init__(self, application=None, filepath=None):
        super().__init__(application=application)

        self.add_css_class("devel")

        self.create_action('preferences', self.on_preferences_action)
        self.create_action('about', self.on_about_action)
        self.create_action('save-as-image', self.open_save_file_chooser)
        self.create_action('open-new', self.open_file_chooser)

        self.window_settings = WindowSettings()

        self.engine = Engine(Window.EXTERNAL)
        self.loader = self.engine.getLoader()
        self.camera = self.engine.window.getCamera()

        self.engine.autoload_plugins()

        self.camera.setFocalPoint((0,0,0))

        if self.window_settings.get_setting("orthographic"):
            self.toggle_orthographic()

        inital_options = {
            "scene.up-direction": "+Y",
            "render.background.color": [1.0, 1.0, 1.0],
            "scene.animation.autoplay": True,
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

        self.style_manager = Adw.StyleManager()
        self.style_manager.connect("notify::dark", self.update_theme)

        if filepath:
            self.open_file(filepath)

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
        if gesture.get_current_button() == 1:
            self.camera.elevation(-(self.drag_prev_offset[1] - y_offset))
            self.camera.azimuth(self.drag_prev_offset[0] - x_offset)
        elif gesture.get_current_button() == 2:
            self.camera.pitch(-(self.drag_prev_offset[1] - y_offset)*0.05)
            self.camera.yaw(-(self.drag_prev_offset[0] - x_offset)*0.05)

        if self.window_settings.get_setting("point-up"):
            self.camera.setViewUp((0.0, 1.0, 0.0))

        print(gesture.get_current_button())

        self.gl_area.queue_render()

        self.drag_prev_offset = (x_offset, y_offset)

    @Gtk.Template.Callback("on_drag_end")
    def on_drag_end(self, gesture, *args):
        self.drag_prev_offset = (0, 0)

    def open_file_chooser(self, *args):
        file_filter = Gtk.FileFilter(name="All supported formats")

        file_patterns = ["*.vtk", "*.vt[p|u|r|i|s|m]", "*.ply", "*.stl", "*.dcm", "*.nrrd",
            "*.nhrd", "*.mhd", "*.mha", "*.tif", "*.tiff", "*.ex2", "*.e", "*.exo", "*.g", "*.gml", "*.pts",
            "*.step", "*.stp", "*.iges", "*.igs", "*.brep", "*.abc", "*.vdb", "*.obj", "*.gltf",
            "*.glb", "*.3ds", "*.wrl", "*.fbx", "*.dae", "*.off", "*.dxf", "*.x", "*.3mf", "*.usd"]

        for patt in file_patterns:
            file_filter.add_pattern(patt)

        filter_list = Gio.ListStore.new(Gtk.FileFilter())
        filter_list.append(file_filter)

        dialog = Gtk.FileDialog(
            title=_("Open File"),
            filters=filter_list,
        )

        dialog.open(self, None, self.on_open_file_response)

    def on_open_file_response(self, dialog, response):
        file = dialog.open_finish(response)

        if file:
            filepath = file.get_path()

            self.open_file(filepath)

    def open_file(self, filepath):
        self.engine.loader.load_scene(filepath)

        self.camera.resetToBounds()
        self.camera.setCurrentAsDefault()

        file_name = os.path.basename(filepath)

        self.title_widget.set_subtitle(file_name)
        self.stack.set_visible_child_name("3d_page")

        GLib.timeout_add(200, self.update_options)

    def update_options(self):
        options = {}
        for key, value in self.window_settings.settings.items():
            try:
                f3d_key = self.keys[key]
            except:
                continue
            options.setdefault(f3d_key, value)

        self.engine.options.update(options)
        self.update_theme()
        self.gl_area.queue_render()

        return False

    def save_as_image(self, filepath):
        self.gl_area.get_context().make_current()
        img = self.engine.window.render_to_image()
        img.save(filepath)

    def open_save_file_chooser(self, *args):
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
            self.window_settings.set_setting("orthographic", True)
        else:
            btn.set_icon_name("perspective-symbolic")
            camera_options = {"scene.camera.orthographic": False}
            self.window_settings.set_setting("orthographic", False)
        self.engine.options.update(camera_options)
        self.gl_area.queue_render()

    def on_switch_toggled(self, switch, active, name):
        self.window_settings.set_setting(name, switch.get_active())
        options = {self.keys[name]: switch.get_active()}
        self.engine.options.update(options)
        self.gl_area.queue_render()

    def on_spin_changed(self, spin, value, name):
        options = {self.keys[name]: spin.get_value()}
        self.window_settings.set_setting(name, spin.get_value())
        self.engine.options.update(options)
        self.gl_area.queue_render()

    def set_point_up(self, switch, active, name):
        val = switch.get_active()
        self.window_settings.set_setting(name, val)
        if val:
            self.camera.setViewUp((0.0, 1.0, 0.0))
            self.gl_area.queue_render()

    def on_direction_changed(self, combo, selected):
        options = {"scene.up-direction": self.up_dirs(selected)}
        self.engine.options.update(options)
        self.window_settings.set_setting("up-direction", selected)

    def on_reset_settings_clicked(self, btn):
        self.engine.options.update(self.window_settings.settings)
        self.gl_area.queue_render()

    def on_save_settings_clicked(self, btn):
        self.window_settings.save_all_settings()

    def on_preferences_action(self, *args):
        preferences = Preferences()

        self.set_preference_values(preferences)

        preferences.translucency_switch.connect("notify::active", self.on_switch_toggled, "translucency")
        preferences.grid_switch.connect("notify::active", self.on_switch_toggled, "grid")
        preferences.tone_mapping_switch.connect("notify::active", self.on_switch_toggled, "tone-mapping")
        preferences.ambient_occlusion_switch.connect("notify::active", self.on_switch_toggled, "ambient-occlusion")
        preferences.anti_aliasing_switch.connect("notify::active", self.on_switch_toggled, "anti-aliasing")
        preferences.hdri_ambient_switch.connect("notify::active", self.on_switch_toggled, "hdri-ambient")

        preferences.point_up_switch.connect("notify::active", self.set_point_up, "point-up")

        preferences.light_intensity_spin.connect("notify::value", self.on_spin_changed, "light-intensity")

        preferences.reset_button.connect("clicked", self.on_reset_settings_clicked)
        preferences.reset_button.connect("clicked", lambda self, btn, pref: self.set_preference_values(pref))

        preferences.save_button.connect("clicked", self.on_save_settings_clicked)

        preferences.present()

    def set_preference_values(self, preferences):
        preferences.translucency_switch.set_active(self.window_settings.get_setting("translucency"))
        preferences.grid_switch.set_active(self.window_settings.get_setting("grid"))
        preferences.tone_mapping_switch.set_active(self.window_settings.get_setting("tone-mapping"))
        preferences.ambient_occlusion_switch.set_active(self.window_settings.get_setting("ambient-occlusion"))
        preferences.anti_aliasing_switch.set_active(self.window_settings.get_setting("anti-aliasing"))
        preferences.hdri_ambient_switch.set_active(self.window_settings.get_setting("hdri-ambient"))
        preferences.point_up_switch.set_active(self.window_settings.get_setting("point-up"))
        preferences.light_intensity_spin.set_value(self.window_settings.get_setting("light-intensity"))

    def create_action(self, name, callback):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)

    def on_about_action(self, *args):
        about = Adw.AboutDialog(
                                application_name='Exhibit',
                                application_icon='io.github.nokse22.Exhibit',
                                developer_name='Nokse22',
                                version='0.1.0',
                                website='https://github.com/Nokse22/Exhibit',
                                issue_url='https://github.com/Nokse22/Exhibit/issues',
                                developers=['Nokse22'],
                                copyright='© 2024 Nokse22')
        about.present(self)
