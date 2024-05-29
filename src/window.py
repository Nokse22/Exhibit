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

up_dir_n_to_string = {
    0: "-X",
    1: "+X",
    2: "-Y",
    3: "+Y",
    4: "-Z",
    5: "+Z"
}

up_dir_string_to_n = {
    "-X": 0,
    "+X": 1,
    "-Y": 2,
    "+Y": 3,
    "-Z": 4,
    "+Z": 5
}

up_dirs_vector = {
    "-X": (-1.0, 0.0, 0.0),
    "+X": (1.0, 0.0, 0.0),
    "-Y": (0.0, -1.0, 0.0),
    "+Y": (0.0, 1.0, 0.0),
    "-Z": (0.0, 0.0, -1.0),
    "+Z": (0.0, 0.0, 1.0)
}

class WindowSettings():
    def __init__(self):
        super().__init__()

        self.saved_settings = Gio.Settings.new('io.github.nokse22.Exhibit')

        self.settings = {
            "grid": self.saved_settings.get_boolean("grid"),
            "absolute-grid": self.saved_settings.get_boolean("absolute-grid"),
            "translucency": self.saved_settings.get_boolean("translucency"),
            "tone-mapping": self.saved_settings.get_boolean("tone-mapping"),
            "ambient-occlusion": self.saved_settings.get_boolean("ambient-occlusion"),
            "anti-aliasing": self.saved_settings.get_boolean("anti-aliasing"),
            "hdri-ambient": self.saved_settings.get_boolean("hdri-ambient"),
            "light-intensity": self.saved_settings.get_double("light-intensity"),
            "orthographic": self.saved_settings.get_boolean("orthographic"),
            "point-up": self.saved_settings.get_boolean("point-up"),
            "skybox-path": "",
            "blur-background": self.saved_settings.get_boolean("blur-background"),
            "blur-coc": self.saved_settings.get_double("blur-coc"),
            "use-skybox": False,
            "background-color": rgb_to_list(self.saved_settings.get_string("background-color")),
            "use-color": self.saved_settings.get_boolean("use-color"),
            "show-edges": self.saved_settings.get_boolean("show-edges"),
            "edges-width": self.saved_settings.get_double("edges-width"),
            "up-direction": self.saved_settings.get_string("up-direction")
        }

    def set_setting(self, key, val):
        self.settings[key] = val

    def get_setting(self, key):
        return self.settings[key]

    def save_all_settings(self):
        self.saved_settings.set_boolean("grid", self.settings["grid"])
        self.saved_settings.set_boolean("absolute-grid", self.settings["absolute-grid"])
        self.saved_settings.set_boolean("translucency", self.settings["translucency"])
        self.saved_settings.set_boolean("tone-mapping", self.settings["tone-mapping"])
        self.saved_settings.set_boolean("ambient-occlusion", self.settings["ambient-occlusion"])
        self.saved_settings.set_boolean("anti-aliasing", self.settings["anti-aliasing"])
        self.saved_settings.set_boolean("hdri-ambient", self.settings["hdri-ambient"])
        self.saved_settings.set_double("light-intensity", self.settings["light-intensity"])
        self.saved_settings.set_boolean("orthographic", self.settings["orthographic"])
        self.saved_settings.set_boolean("point-up", self.settings["point-up"])
        self.saved_settings.set_boolean("blur-background", self.settings["blur-background"])
        self.saved_settings.set_double("blur-coc", self.settings["blur-coc"])
        self.saved_settings.set_boolean("use-color", self.settings["use-color"])
        self.saved_settings.set_string("background-color", list_to_rgb(self.settings["background-color"]))
        self.saved_settings.set_double("edges-width", self.settings["edges-width"])
        self.saved_settings.set_string("up-direction", self.settings["up-direction"])

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
        "absolute-grid": "render.grid.absolute",
        "translucency": "render.effect.translucency-support",
        "tone-mapping":"render.effect.tone-mapping",
        "ambient-occlusion": "render.effect.ambient-occlusion",
        "anti-aliasing" :"render.effect.anti-aliasing",
        "hdri-ambient" :"render.hdri.ambient",
        "background-skybox": "render.background.skybox",
        "background-blur": "background.blur",
        "light-intensity": "render.light.intensity",
        "orthographic": "scene.camera.orthographic",
        "blur-background": "render.background.blur",
        "blur-coc": "render.background.blur.coc",
        "use-skybox": "render.background.skybox",
        "background-color": "render.background.color",
        "show-edges": "render.show-edges",
        "edges-width": "render.line-width",
        "up-direction": "scene.up-direction",
    }

    preference_window = None
    width = 600
    height = 600
    distance = 0

    file_name = ""

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
            "render.background.color": [1.0, 1.0, 1.0],
            "scene.up-direction": self.window_settings.get_setting("up-direction")
        }

        self.engine.options.update(inital_options)

        self.gl_area.set_auto_render(True)
        self.gl_area.connect("realize", self.on_realize)
        self.gl_area.connect("render", self.on_render)
        self.gl_area.connect("resize", self.on_resize)

        self.gl_area.set_allowed_apis(Gdk.GLAPI.GL)
        # self.gl_area.set_required_version(1, 0)

        self.prev_pan_offset = 0
        self.drag_prev_offset = (0, 0)
        self.drag_start_angle = 0

        self.style_manager = Adw.StyleManager()
        self.style_manager.connect("notify::dark", self.update_background_color)

        if filepath:
            self.filepath = filepath
            self.load_file()

        # self.update_options()

    def on_resize(self, gl_area, width, heigh):
        self.width = width
        self.height = heigh

    def on_realize(self, area):
        self.gl_area.get_context().make_current()

    def on_render(self, area, ctx):
        self.gl_area.get_context().make_current()
        self.engine.window.render()
        return True

    @Gtk.Template.Callback("on_scroll")
    def on_scroll(self, gesture, dx, dy):
        if self.window_settings.get_setting("orthographic"):
            self.engine.options.update({"scene.camera.orthographic": False})
            self.gl_area.get_context().make_current()
            self.engine.window.render_to_image()
            self.camera.dolly(1 - 0.1*dy)
            self.engine.options.update({"scene.camera.orthographic": self.window_settings.settings["orthographic"]})
        else:
            self.camera.dolly(1 - 0.1*dy)
        self.get_distance()
        self.gl_area.queue_render()

    @Gtk.Template.Callback("on_drag_update")
    def on_drag_update(self, gesture, x_offset, y_offset):
        if gesture.get_current_button() == 1:
            self.camera.elevation(-(self.drag_prev_offset[1] - y_offset))
            self.camera.azimuth(self.drag_prev_offset[0] - x_offset)
        elif gesture.get_current_button() == 2:
            w = v_norm(v_sub(self.camera.focal_point, self.camera.position))
            v = self.camera.view_up
            u = v_cross(v, w)
            delta = v_add(
                v_mul(u, -(self.drag_prev_offset[0] - x_offset) * (0.0000001*self.width + 0.001*self.distance)),
                v_mul(v, -(self.drag_prev_offset[1] - y_offset) * (0.0000001*self.height + 0.001*self.distance)),
            )
            self.camera.position = v_add(self.camera.position, delta)
            self.camera.focal_point = v_add(self.camera.focal_point, delta)

        if self.window_settings.get_setting("point-up"):
            up = up_dirs_vector[self.window_settings.get_setting("up-direction")]
            self.camera.setViewUp(up)

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
            self.filepath = file.get_path()

            self.load_file()

    def load_file(self):
        try:
            self.engine.loader.load_scene(self.filepath)
        except:
            self.engine.loader.load_geometry(self.filepath, True)

        self.camera.resetToBounds()
        self.camera.setCurrentAsDefault()

        self.get_distance()

        self.file_name = os.path.basename(self.filepath)

        self.set_title(f"View {self.file_name}")
        self.title_widget.set_title("Exhibit")
        self.title_widget.set_subtitle(self.file_name)
        self.stack.set_visible_child_name("3d_page")

        GLib.timeout_add(100, self.update_options)

    def update_options(self):
        options = {}
        for key, value in self.window_settings.settings.items():
            try:
                f3d_key = self.keys[key]
            except:
                continue
            options.setdefault(f3d_key, value)

        self.engine.options.update(options)
        self.update_background_color()
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

    def front_view(self, *args):
        self.camera.position = v_add(self.camera.focal_point, (0, 0, 100))
        self.camera.setViewUp(up_dirs_vector[self.window_settings.get_setting("up-direction")])
        self.camera.resetToBounds()
        self.gl_area.queue_render()

    def right_view(self, *args):
        self.camera.position = v_add(self.camera.focal_point, (100, 0, 0))
        self.camera.setViewUp(up_dirs_vector[self.window_settings.get_setting("up-direction")])
        self.camera.resetToBounds()
        self.gl_area.queue_render()

    def top_view(self, *args):
        self.camera.position = v_add(self.camera.focal_point, (0, 100, 0))
        self.camera.setViewUp((0.0, 0.0, -1.0))
        self.camera.resetToBounds()
        self.gl_area.queue_render()

    def isometric_view(self, *args):
        self.camera.position = v_add(self.camera.focal_point, (100, 100 , 100))
        self.camera.setViewUp(up_dirs_vector[self.window_settings.get_setting("up-direction")])
        self.camera.resetToBounds()
        self.gl_area.queue_render()

    @Gtk.Template.Callback("on_home_clicked")
    def on_home_clicked(self, btn):
        self.camera.resetToDefault()
        self.get_distance()
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
            self.camera.setViewUp(up_dirs_vector[self.window_settings.get_setting("up-direction")])
            self.gl_area.queue_render()

    def get_distance(self):
        self.distance = p_dist(self.camera.position, (0,0,0))

    def on_reset_settings_clicked(self, btn):
        self.engine.options.update(self.window_settings.settings)
        self.gl_area.queue_render()

    def on_save_settings_clicked(self, btn):
        self.window_settings.save_all_settings()

    def on_preferences_action(self, *args):
        if self.preference_window:
            self.preference_window.present()
            return

        preferences = Preferences()
        preferences.set_title(f"Preferences {self.file_name}")
        preferences.connect("close-request", self.on_preferences_close)

        self.set_preference_values(preferences)

        preferences.grid_switch.connect("notify::active", self.on_switch_toggled, "grid")
        preferences.absolute_grid_switch.connect("notify::active", self.on_switch_toggled, "absolute-grid")

        preferences.translucency_switch.connect("notify::active", self.on_switch_toggled, "translucency")
        preferences.tone_mapping_switch.connect("notify::active", self.on_switch_toggled, "tone-mapping")
        preferences.ambient_occlusion_switch.connect("notify::active", self.on_switch_toggled, "ambient-occlusion")
        preferences.anti_aliasing_switch.connect("notify::active", self.on_switch_toggled, "anti-aliasing")
        preferences.hdri_ambient_switch.connect("notify::active", self.on_switch_toggled, "hdri-ambient")

        preferences.edges_switch.connect("notify::active", self.on_switch_toggled, "show-edges")
        preferences.edges_width_spin.connect("notify::value", self.on_spin_changed, "edges-width")

        preferences.light_intensity_spin.connect("notify::value", self.on_spin_changed, "light-intensity")

        preferences.use_skybox_switch.connect("notify::active", self.on_switch_toggled, "use-skybox")
        preferences.open_skybox_button.connect("clicked", self.on_open_skybox_clicked)
        preferences.blur_switch.connect("notify::active", self.on_switch_toggled, "blur-background")
        preferences.blur_coc_spin.connect("notify::value", self.on_spin_changed, "blur-coc")

        preferences.use_color_switch.connect("notify::active", self.update_background_color)
        preferences.use_color_switch.connect("notify::active",
                lambda switch, *args: self.window_settings.set_setting("use-color", switch.get_active())
        )
        preferences.background_color_button.connect("notify::rgba", self.update_background_color)
        preferences.background_color_button.connect("notify::rgba",
                lambda btn, *args: self.window_settings.set_setting("background-color", rgb_to_list(btn.get_rgba().to_string()))
        )

        preferences.point_up_switch.connect("notify::active", self.set_point_up, "point-up")
        preferences.up_direction_combo.connect("notify::selected", self.set_up_direction)

        preferences.reset_button.connect("clicked", self.on_reset_settings_clicked)
        preferences.reset_button.connect("clicked", lambda self, btn, pref: self.set_preference_values(pref))

        preferences.save_button.connect("clicked", self.on_save_settings_clicked)

        preferences.present()

        self.preference_window = preferences

    def set_up_direction(self, combo, *args):
        direction = up_dir_n_to_string[combo.get_selected()]
        options = {"scene.up-direction": direction}
        self.engine.options.update(options)
        self.load_file()
        self.window_settings.set_setting("up-direction", direction)

    def update_background_color(self, *args):
        if self.preference_window:
            if self.preference_window.use_color_switch.get_active():
                options = {
                    "render.background.color": rgb_to_list(self.preference_window.background_color_button.get_rgba().to_string()),
                }
                self.engine.options.update(options)
                self.gl_area.queue_render()
                return
        if self.style_manager.get_dark():
            options = {"render.background.color": [0.2, 0.2, 0.2]}
        else:
            options = {"render.background.color": [1.0, 1.0, 1.0]}
        self.engine.options.update(options)
        self.gl_area.queue_render()

    def on_open_skybox_clicked(self, *args):
        file_filter = Gtk.FileFilter(name="All supported formats")

        file_patterns = ["*.hdr", "*.exr", "*.png", "*.jpg", "*.pnm", "*.tiff", "*.bmp"]

        for patt in file_patterns:
            file_filter.add_pattern(patt)

        filter_list = Gio.ListStore.new(Gtk.FileFilter())
        filter_list.append(file_filter)

        dialog = Gtk.FileDialog(
            title=_("Open Skybox File"),
            filters=filter_list,
        )

        dialog.open(self, None, self.on_open_skybox_file_response)

    def on_open_skybox_file_response(self, dialog, response):
        file = dialog.open_finish(response)

        if file:
            filepath = file.get_path()

            self.window_settings.set_setting("skybox-path", filepath)
            options = {"render.hdri.file": filepath}
            self.engine.options.update(options)
            self.preference_window.skybox_row.set_text(filepath)

            self.gl_area.queue_render()

    def on_preferences_close(self, *args):
        self.preference_window = None

    def set_preference_values(self, preferences):
        preferences.grid_switch.set_active(self.window_settings.get_setting("grid"))
        preferences.absolute_grid_switch.set_active(self.window_settings.get_setting("absolute-grid"))

        preferences.translucency_switch.set_active(self.window_settings.get_setting("translucency"))
        preferences.tone_mapping_switch.set_active(self.window_settings.get_setting("tone-mapping"))
        preferences.ambient_occlusion_switch.set_active(self.window_settings.get_setting("ambient-occlusion"))
        preferences.anti_aliasing_switch.set_active(self.window_settings.get_setting("anti-aliasing"))
        preferences.hdri_ambient_switch.set_active(self.window_settings.get_setting("hdri-ambient"))
        preferences.light_intensity_spin.set_value(self.window_settings.get_setting("light-intensity"))
        preferences.skybox_row.set_text(self.window_settings.get_setting("skybox-path"))
        preferences.blur_switch.set_active(self.window_settings.get_setting("blur-background"))
        preferences.blur_coc_spin.set_value(self.window_settings.get_setting("blur-coc"))
        preferences.use_skybox_switch.set_active(self.window_settings.get_setting("use-skybox"))

        preferences.edges_switch.set_active(self.window_settings.get_setting("show-edges"))
        preferences.edges_width_spin.set_value(self.window_settings.get_setting("edges-width"))

        preferences.point_up_switch.set_active(self.window_settings.get_setting("point-up"))
        preferences.up_direction_combo.set_selected(up_dir_string_to_n[self.window_settings.get_setting("up-direction")])

        preferences.use_color_switch.set_active(self.window_settings.get_setting("use-color"))
        print(self.window_settings.get_setting("use-color"))
        rgba = Gdk.RGBA()
        rgba.parse(list_to_rgb(self.window_settings.get_setting("background-color")))
        preferences.background_color_button.set_rgba(rgba)

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
                                copyright='© 2024 Nokse22',
                                artists=["Jakub Steiner https://jimmac.eu"])
        about.present(self)

def p_dist(point1, point2):
    if len(point1) != len(point2):
        raise ValueError("Points must have the same dimension")

    squared_diffs = [(x - y) ** 2 for x, y in zip(point1, point2)]
    return math.sqrt(sum(squared_diffs))

def v_norm(vector):
    norm = math.sqrt(sum(x**2 for x in vector))
    return tuple(x / norm for x in vector)

def v_add(vector1, vector2):
    return tuple(v1 + v2 for v1, v2 in zip(vector1, vector2))

def v_sub(vector1, vector2):
    return tuple(v1 - v2 for v1, v2 in zip(vector1, vector2))

def v_mul(vector, scalar):
    return tuple(v * scalar for v in vector)

def v_cross(vector1, vector2):
    if len(vector1) != 3 or len(vector2) != 3:
        raise ValueError("Cross product is defined only for 3-dimensional vectors.")

    x = vector1[1] * vector2[2] - vector1[2] * vector2[1]
    y = vector1[2] * vector2[0] - vector1[0] * vector2[2]
    z = vector1[0] * vector2[1] - vector1[1] * vector2[0]

    return (x, y, z)

def rgb_to_list(rgb):
    values = [int(x) / 255 for x in rgb[4:-1].split(',')]
    return values

def list_to_rgb(lst):
    return f"rgb({int(lst[0] * 255)},{int(lst[1] * 255)},{int(lst[2] * 255)})"
