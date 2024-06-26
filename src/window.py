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
from gi.repository import Gtk, Gdk, Gio, GLib, GObject

from .widgets import *

import f3d
from f3d import *

import math
import os
import threading
import datetime

from wand.image import Image

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

file_patterns = ["*.vtk", "*.vtp", "*.vtu", "*.vtr", "*.vti", "*.vts", "*.vtm", "*.ply", "*.stl", "*.dcm", "*.drc", "*.nrrd",
    "*.nhrd", "*.mhd", "*.mha", "*.ex2", "*.e", "*.exo", "*.g", "*.gml", "*.pts",
    "*.ply", "*.step", "*.stp", "*.iges", "*.igs", "*.brep", "*.abc", "*.vdb", "*.obj", "*.gltf",
    "*.glb", "*.3ds", "*.wrl", "*.fbx", "*.dae", "*.off", "*.dxf", "*.x", "*.3mf", "*.usd", "*.usda", "*.usdc", "*.usdz"]

image_patterns = ["*.hdr", "*.exr", "*.png", "*.jpg", "*.pnm", "*.tiff", "*.bmp"]

class WindowSettings():
    def __init__(self):
        super().__init__()

        self.saved_settings = Gio.Settings.new('io.github.nokse22.Exhibit')

        self.settings = None

        self.load_settings()

    def load_settings(self):
        self.settings = {
            "grid": self.saved_settings.get_boolean("grid"),
            "absolute-grid": self.saved_settings.get_boolean("absolute-grid"),
            "translucency": self.saved_settings.get_boolean("translucency"),
            "tone-mapping": self.saved_settings.get_boolean("tone-mapping"),
            "ambient-occlusion": self.saved_settings.get_boolean("ambient-occlusion"),
            "anti-aliasing": self.saved_settings.get_boolean("anti-aliasing"),
            "hdri-ambient": False, # self.saved_settings.get_boolean("hdri-ambient"),
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
            "up-direction": self.saved_settings.get_string("up-direction"),
            "auto-up-dir" : self.saved_settings.get_boolean("auto-up-dir"),
            "show-points": self.saved_settings.get_boolean("show-points"),
            "point-size": self.saved_settings.get_double("point-size"),
            "model-color": rgb_to_list(self.saved_settings.get_string("model-color")),
            "model-metallic": self.saved_settings.get_double("model-metallic"),
            "model-roughness": self.saved_settings.get_double("model-roughness"),
            "model-opacity": self.saved_settings.get_double("model-opacity"),
            "load-type": None # 0 for geometry and 1 for scene
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
        # self.saved_settings.set_boolean("hdri-ambient", self.settings["hdri-ambient"])
        self.saved_settings.set_double("light-intensity", self.settings["light-intensity"])
        self.saved_settings.set_boolean("orthographic", self.settings["orthographic"])
        self.saved_settings.set_boolean("point-up", self.settings["point-up"])
        self.saved_settings.set_boolean("blur-background", self.settings["blur-background"])
        self.saved_settings.set_double("blur-coc", self.settings["blur-coc"])
        self.saved_settings.set_boolean("use-color", self.settings["use-color"])
        self.saved_settings.set_string("background-color", list_to_rgb(self.settings["background-color"]))
        self.saved_settings.set_double("edges-width", self.settings["edges-width"])
        self.saved_settings.set_string("up-direction", self.settings["up-direction"])
        self.saved_settings.set_boolean("auto-up-dir", self.settings["auto-up-dir"])
        self.saved_settings.set_string("model-color", list_to_rgb(self.settings["model-color"]))
        self.saved_settings.set_double("model-metallic", self.settings["model-metallic"])
        self.saved_settings.set_double("model-roughness", self.settings["model-roughness"])
        self.saved_settings.set_boolean("show-points", self.settings["show-points"])
        self.saved_settings.set_double("model-opacity", self.settings["model-opacity"])

    def reset_all(self):
        for key in self.settings:
            self.saved_settings.reset(key)
        self.load_settings()
        self.save_all_settings()

@Gtk.Template(resource_path='/io/github/nokse22/Exhibit/ui/window.ui')
class Viewer3dWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'Viewer3dWindow'

    split_view = Gtk.Template.Child()

    gl_area = Gtk.Template.Child()

    title_widget = Gtk.Template.Child()
    stack = Gtk.Template.Child()
    toolbar_view = Gtk.Template.Child()

    view_button_headerbar = Gtk.Template.Child()

    drop_revealer = Gtk.Template.Child()
    view_drop_target = Gtk.Template.Child()
    loading_drop_target = Gtk.Template.Child()

    toast_overlay = Gtk.Template.Child()

    grid_switch = Gtk.Template.Child()
    absolute_grid_switch = Gtk.Template.Child()

    translucency_switch = Gtk.Template.Child()
    tone_mapping_switch = Gtk.Template.Child()
    ambient_occlusion_switch = Gtk.Template.Child()
    anti_aliasing_switch = Gtk.Template.Child()
    hdri_ambient_switch = Gtk.Template.Child()
    light_intensity_spin = Gtk.Template.Child()

    edges_switch = Gtk.Template.Child()
    edges_width_spin = Gtk.Template.Child()

    use_skybox_switch = Gtk.Template.Child()

    hdri_file_row = Gtk.Template.Child()
    blur_switch = Gtk.Template.Child()
    blur_coc_spin = Gtk.Template.Child()

    use_color_switch = Gtk.Template.Child()
    background_color_button = Gtk.Template.Child()

    point_up_switch = Gtk.Template.Child()
    up_direction_combo = Gtk.Template.Child()

    reset_button = Gtk.Template.Child()
    save_button = Gtk.Template.Child()
    restore_button = Gtk.Template.Child()

    automatic_up_direction_switch = Gtk.Template.Child()

    points_group = Gtk.Template.Child()
    points_expander = Gtk.Template.Child()
    points_size_spin = Gtk.Template.Child()

    model_load_combo = Gtk.Template.Child()

    material_group = Gtk.Template.Child()

    model_roughness_spin = Gtk.Template.Child()
    model_metallic_spin = Gtk.Template.Child()
    model_color_button = Gtk.Template.Child()
    model_opacity_spin = Gtk.Template.Child()

    startup_stack = Gtk.Template.Child()

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
        "show-points": "model.point-sprites.enable",
        "point-size": "render.point-size",
        "model-color": "model.color.rgb",
        "model-metallic": "model.material.metallic",
        "model-roughness": "model.material.roughness",
        "model-opacity": "model.color.opacity"
    }

    width = 600
    height = 600
    distance = 0

    file_name = ""

    def __init__(self, application=None, startup_filepath=None):
        super().__init__(application=application)

        self.save_as_action = self.create_action('save-as-image', self.open_save_file_chooser)

        self.open_new_action = self.create_action('open-new', self.open_file_chooser)

        self.view_drop_target.set_gtypes([Gdk.FileList])
        self.loading_drop_target.set_gtypes([Gdk.FileList])

        self.window_settings = WindowSettings()
        settings = Gio.Settings.new('io.github.nokse22.Exhibit')

        self.set_default_size(settings.get_int("startup-width"), settings.get_int("startup-height"))
        self.split_view.set_show_sidebar(settings.get_boolean("startup-sidebar-show"))

        self.set_preference_values(False)

        self.grid_switch.connect("notify::active", self.on_switch_toggled, "grid")
        self.absolute_grid_switch.connect("notify::active", self.on_switch_toggled, "absolute-grid")

        self.translucency_switch.connect("notify::active", self.on_switch_toggled, "translucency")
        self.tone_mapping_switch.connect("notify::active", self.on_switch_toggled, "tone-mapping")
        self.ambient_occlusion_switch.connect("notify::active", self.on_switch_toggled, "ambient-occlusion")
        self.anti_aliasing_switch.connect("notify::active", self.on_switch_toggled, "anti-aliasing")
        self.hdri_ambient_switch.connect("notify::active", self.on_switch_toggled, "hdri-ambient")

        self.edges_switch.connect("notify::active", self.on_switch_toggled, "show-edges")
        self.edges_width_spin.connect("notify::value", self.on_spin_changed, "edges-width")

        self.points_expander.connect("notify::enable-expansion", self.on_expander_toggled, "show-points")
        self.points_size_spin.connect("notify::value", self.on_spin_changed, "point-size")

        self.load_type_combo_handler_id = self.model_load_combo.connect("notify::selected", self.set_load_type)
        self.model_roughness_spin.connect("notify::value", self.on_spin_changed, "model-roughness")
        self.model_metallic_spin.connect("notify::value", self.on_spin_changed, "model-metallic")
        self.model_color_button.connect("notify::rgba", self.on_color_changed, "model-color")
        self.model_opacity_spin.connect("notify::value", self.on_spin_changed, "model-opacity")

        self.light_intensity_spin.connect("notify::value", self.on_spin_changed, "light-intensity")

        self.use_skybox_switch.connect("notify::active", self.on_switch_toggled, "use-skybox")

        self.hdri_file_row.connect("open-file", self.on_open_skybox)
        self.hdri_file_row.connect("delete-file", self.on_delete_skybox)
        self.hdri_file_row.connect("file-added", lambda row, filepath: self.load_hdri(filepath))

        self.hdri_path = os.environ["XDG_DATA_HOME"] + "/HDRIs/"
        self.hdri_thumbnails_path = self.hdri_path + "/thumbnails/"

        os.makedirs(self.hdri_path, exist_ok=True)
        os.makedirs(self.hdri_thumbnails_path, exist_ok=True)

        for filename in list_files(self.hdri_path):
            name, _ = os.path.splitext(filename)

            thumbnail = self.hdri_thumbnails_path + name + ".jpeg"
            filepath = self.hdri_path + filename
            try:
                if not os.path.isfile(thumbnail):
                    thumbnail = self.generate_thumbnail(filepath)
                self.hdri_file_row.add_suggested_file(thumbnail, filepath)
            except Exception as e:
                print("Couldn't open HDRI file, skipping")

        self.blur_switch.connect("notify::active", self.on_switch_toggled, "blur-background")
        self.blur_coc_spin.connect("notify::value", self.on_spin_changed, "blur-coc")

        self.use_color_switch.connect("notify::active",
                lambda switch, *args: self.window_settings.set_setting("use-color", switch.get_active())
        )
        self.use_color_switch.connect("notify::active", self.update_background_color)

        self.background_color_button.connect("notify::rgba", self.on_color_changed, "background-color")
        self.background_color_button.connect("notify::rgba",
                lambda *args: self.update_background_color()
        )

        self.point_up_switch.connect("notify::active", self.set_point_up, "point-up")
        self.up_direction_combo_handler_id = self.up_direction_combo.connect("notify::selected", self.set_up_direction)

        self.reset_button.connect("clicked", self.on_reset_settings_clicked)
        self.restore_button.connect("clicked", self.on_restore_settings_clicked)
        self.save_button.connect("clicked", self.on_save_settings_clicked)

        self.automatic_up_direction_switch.connect("notify::active",
                lambda switch, *args: self.window_settings.set_setting("auto-up-dir", switch.get_active())
        )

        self.engine = Engine(Window.EXTERNAL)
        self.loader = self.engine.getLoader()
        self.camera = self.engine.window.getCamera()

        self.engine.autoload_plugins()

        self.camera.setFocalPoint((0,0,0))

        if self.window_settings.get_setting("orthographic"):
            self.toggle_orthographic()

        initial_options = {
            "scene.up-direction": self.window_settings.get_setting("up-direction"),
        }

        self.engine.options.update(initial_options)

        self.gl_area.set_auto_render(True)
        self.gl_area.connect("realize", self.on_realize)
        self.gl_area.connect("render", self.on_render)
        self.gl_area.connect("resize", self.on_resize)

        self.gl_area.set_allowed_apis(Gdk.GLAPI.GL)
        # self.gl_area.set_required_version(1, 0)

        self.prev_pan_offset = 0
        self.drag_prev_offset = (0, 0)
        self.drag_start_angle = 0

        self.prev_scale = 1

        self.no_file_loaded = True

        self.style_manager = Adw.StyleManager().get_default()
        self.style_manager.connect("notify::dark", self.update_background_color)

        self.update_background_color()

        if startup_filepath:
            print("start file")
            self.load_file(startup_filepath)

    def on_resize(self, gl_area, width, height):
        self.width = width
        self.height = height

    def on_realize(self, area):
        if self.gl_area.get_context() is None:
            print("Could not create GL context")

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

    @Gtk.Template.Callback("on_zoom_scale_changed")
    def on_zoom_scale_changed(self, zoom_gesture, scale):
        self.camera.dolly(1 - self.prev_scale + scale)
        self.prev_scale = scale
        self.get_distance()
        self.gl_area.queue_render()

    @Gtk.Template.Callback("on_drag_update")
    def on_drag_update(self, gesture, x_offset, y_offset):
        if gesture.get_current_button() == 1:
            dist, direction = self.get_camera_to_focal_distance()
            y = -(self.drag_prev_offset[1] - y_offset) * 0.5
            x = (self.drag_prev_offset[0] - x_offset) * 0.5
            if not self.window_settings.get_setting("point-up"):
                self.camera.elevation(y)
                self.camera.azimuth(x)
            else:
                if (dist > self.get_gimble_limit() or (dist < self.get_gimble_limit()) and
                        (direction == 1 and y < 0) or (dist < self.get_gimble_limit() and direction == -1 and y > 0)):
                    self.camera.elevation(y)
                self.camera.azimuth(x)
        elif gesture.get_current_button() == 2:
            self.camera.pan(
                (self.drag_prev_offset[0] - x_offset) * (0.0000001*self.width + 0.001*self.distance),
                -(self.drag_prev_offset[1] - y_offset) * (0.0000001*self.height + 0.001*self.distance),
                0
            )

        if self.window_settings.get_setting("point-up"):
            up = up_dirs_vector[self.window_settings.get_setting("up-direction")]
            self.camera.setViewUp(up)

        self.gl_area.queue_render()

        self.drag_prev_offset = (x_offset, y_offset)

    @Gtk.Template.Callback("on_drag_end")
    def on_drag_end(self, gesture, *args):
        self.drag_prev_offset = (0, 0)

    @Gtk.Template.Callback("on_key_pressed")
    def on_key_pressed(self, controller, keyval, keycode, state):
        val = self.distance / 40

        focal_point = self.camera.focal_point

        match keycode:
            case 25:
                self.camera.pan(0, 0, val)
            case 38:
                self.camera.pan(-val, 0, 0)
            case 39:
                self.camera.pan(0, 0, -val)
            case 40:
                self.camera.pan(val, 0, 0)
            case 113:
                self.camera.pan(-val, 0, 0)
                self.camera.focal_point = focal_point
            case 114:
                self.camera.pan(val, 0, 0)
                self.camera.focal_point = focal_point
            case 111:
                dist, direction = self.get_camera_to_focal_distance()
                if dist > self.get_gimble_limit() or (dist < self.get_gimble_limit() and direction == -1):
                    self.camera.pan(0, val, 0)
                    self.camera.focal_point = focal_point
            case 116:
                dist, direction = self.get_camera_to_focal_distance()
                if dist > self.get_gimble_limit() or (dist < self.get_gimble_limit() and direction == 1):
                    self.camera.pan(0, -val, 0)
                    self.camera.focal_point = focal_point

        if self.window_settings.get_setting("point-up"):
            up = up_dirs_vector[self.window_settings.get_setting("up-direction")]
            self.camera.setViewUp(up)

        self.gl_area.queue_render()

    def get_gimble_limit(self):
        return self.distance / 10

    def get_camera_to_focal_distance(self):
        up = up_dirs_vector[self.window_settings.get_setting("up-direction")]
        pos = self.camera.position
        foc = self.camera.focal_point

        pos_proj = v_sub(v_dot_p(pos, v_abs(up)), pos)
        foc_proj = v_sub(v_dot_p(foc, v_abs(up)), foc)

        dist = p_dist(pos_proj, foc_proj)

        pos_height = v_dot_p(pos, v_abs(up))
        foc_height = v_dot_p(foc, v_abs(up))

        diff = v_sub(pos_height, foc_height)

        for number in diff:
            if number != 0:
                return dist, (1 if number > 0 else -1)
        return dist, 1

    def open_file_chooser(self, *args):
        file_filter = Gtk.FileFilter(name="All supported formats")

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
            self.window_settings.set_setting("load-type", None)
            print("open file")
            self.load_file(filepath)

    def load_file(self, filepath=None, override=False):
        if filepath is None:
            filepath = self.filepath

        if self.window_settings.get_setting("auto-up-dir") and not override:
            up = get_up_from_path(filepath)
            self.window_settings.set_setting("up-direction", up)

        options = {"scene.up-direction": self.window_settings.get_setting("up-direction")}
        self.engine.options.update(options)

        def _load():
            scene_loaded = False
            geometry_loaded = False

            if self.window_settings.get_setting("load-type") is None:
                if self.engine.loader.hasSceneReader(filepath):
                    self.engine.loader.load_scene(filepath)
                    scene_loaded = True
                    GLib.idle_add(self.model_load_combo.set_sensitive, True)
                elif self.engine.loader.hasGeometryReader(filepath):
                    self.engine.loader.load_geometry(filepath, True)
                    geometry_loaded = True
                    GLib.idle_add(self.model_load_combo.set_sensitive, False)

            elif self.window_settings.get_setting("load-type") == 0:
                if self.engine.loader.hasGeometryReader(filepath):
                    self.engine.loader.load_geometry(filepath, True)
                    geometry_loaded = True
            elif self.window_settings.get_setting("load-type") == 1:
                if self.engine.loader.hasSceneReader(filepath):
                    self.engine.loader.load_scene(filepath)
                    scene_loaded = True

            if not scene_loaded and not geometry_loaded:
                GLib.idle_add(self.on_file_not_opened, filepath)
                return

            if self.engine.loader.hasGeometryReader(filepath) and self.engine.loader.hasSceneReader(filepath):
                GLib.idle_add(self.model_load_combo.set_sensitive, True)
            else:
                GLib.idle_add(self.model_load_combo.set_sensitive, False)

            if scene_loaded:
                self.window_settings.set_setting("load-type", 1)
            elif geometry_loaded:
                self.window_settings.set_setting("load-type", 0)

            self.camera.resetToBounds()
            self.get_distance()
            self.update_options()

            self.filepath = filepath
            GLib.idle_add(self.on_file_opened)

        threading.Thread(target=_load, daemon=True).start()

    def on_file_opened(self):
        print("on file opened")

        self.file_name = os.path.basename(self.filepath)

        self.set_title(f"View {self.file_name}")
        self.title_widget.set_subtitle(self.file_name)
        self.stack.set_visible_child_name("3d_page")

        self.no_file_loaded = False

        self.drop_revealer.set_reveal_child(False)
        self.toast_overlay.remove_css_class("blurred")

        if self.window_settings.get_setting("load-type") == 0:
            self.material_group.set_sensitive(True)
            self.points_group.set_sensitive(True)
        elif self.window_settings.get_setting("load-type") == 1:
            self.material_group.set_sensitive(False)
            self.points_group.set_sensitive(False)
            self.window_settings.set_setting("show-points", False)

        self.set_preference_values()

    def on_file_not_opened(self, filepath):
        print("on file not opened")
        self.set_title(_("Exhibit"))
        if self.no_file_loaded:
            self.stack.set_visible_child_name("startup_page")
            self.startup_stack.set_visible_child_name("error_page")
        else:
            self.send_toast(_("Can't open") + " " + os.path.basename(filepath))
        options = {"scene.up-direction": self.window_settings.get_setting("up-direction")}
        self.engine.options.update(options)

    def send_toast(self, message):
        toast = Adw.Toast(title=message, timeout=2)
        self.toast_overlay.add_toast(toast)

    def update_options(self):
        options = {}
        for key, value in self.window_settings.settings.items():
            if key in self.keys:
                f3d_key = self.keys[key]
            options.setdefault(f3d_key, value)

        self.engine.options.update(options)
        self.update_background_color()

    def save_as_image(self, filepath):
        self.gl_area.get_context().make_current()
        img = self.engine.window.render_to_image()
        img.save(filepath)

    def open_save_file_chooser(self, *args):
        dialog = Gtk.FileDialog(
            title=_("Save File"),
            initial_name=self.file_name.split(".")[0] + ".png",
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
            toast = Adw.Toast(
                title="Image Saved",
                timeout=2,
                button_label="Open",
                action_name="app.show-image-externally",
                action_target=GLib.Variant("s", file_path)
            )
            self.toast_overlay.add_toast(toast)

    def front_view(self, *args):
        up_v = up_dirs_vector[self.window_settings.get_setting("up-direction")]
        vector = v_mul(tuple([up_v[2], up_v[0], up_v[1]]), 1000)
        self.camera.position = v_add(self.camera.focal_point, vector)
        self.camera.setViewUp(up_dirs_vector[self.window_settings.get_setting("up-direction")])
        self.camera.resetToBounds()
        self.get_distance()
        self.gl_area.queue_render()

    def right_view(self, *args):
        up_v = up_dirs_vector[self.window_settings.get_setting("up-direction")]
        vector = v_mul(tuple([up_v[1], up_v[2], up_v[0]]), 1000)
        self.camera.position = v_add(self.camera.focal_point, vector)
        self.camera.setViewUp(up_dirs_vector[self.window_settings.get_setting("up-direction")])
        self.camera.resetToBounds()
        self.get_distance()
        self.gl_area.queue_render()

    def top_view(self, *args):
        up_v = up_dirs_vector[self.window_settings.get_setting("up-direction")]
        vector = v_mul(up_v, 1000)
        self.camera.position = v_add(self.camera.focal_point, vector)
        vector = v_mul(tuple([up_v[1], up_v[2], up_v[0]]), 1000)
        self.camera.setViewUp(vector)
        self.camera.resetToBounds()
        self.get_distance()
        self.gl_area.queue_render()

    def isometric_view(self, *args):
        up_v = up_dirs_vector[self.window_settings.get_setting("up-direction")]
        vector = v_add(tuple([up_v[2], up_v[0], up_v[1]]), tuple([up_v[1], up_v[2], up_v[0]]))
        self.camera.position = v_mul(v_norm(v_add(vector, up_v)), 1000)
        self.camera.setViewUp(up_dirs_vector[self.window_settings.get_setting("up-direction")])
        self.camera.resetToBounds()
        self.get_distance()
        self.gl_area.queue_render()

    @Gtk.Template.Callback("on_home_clicked")
    def on_home_clicked(self, btn):
        self.camera.resetToBounds()
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

    @Gtk.Template.Callback("on_drop_received")
    def on_drop_received(self, drop, value, x, y):
        filepath = value.get_files()[0].get_path()
        extension = os.path.splitext(filepath)[1][1:]

        if "*." + extension in image_patterns:
            self.load_hdri(filepath)
        else:
            self.window_settings.set_setting("load-type", None)
            self.load_file(filepath)

    @Gtk.Template.Callback("on_drop_enter")
    def on_drop_enter(self, drop_target, *args):
        self.drop_revealer.set_reveal_child(True)
        self.toast_overlay.add_css_class("blurred")

    @Gtk.Template.Callback("on_drop_leave")
    def on_drop_leave(self, *args):
        self.drop_revealer.set_reveal_child(False)
        self.toast_overlay.remove_css_class("blurred")

    @Gtk.Template.Callback("on_close_sidebar_clicked")
    def on_close_sidebar_clicked(self, *args):
        self.split_view.set_show_sidebar(False)

    @Gtk.Template.Callback("on_open_with_external_app_clicked")
    def on_open_with_external_app_clicked(self, *args):
        try:
            file = Gio.File.new_for_path(self.filepath)
        except GLib.GError as e:
            print("Failed to construct a new Gio.File object from path.")
        else:
            launcher = Gtk.FileLauncher.new(file)

            def open_file_finish(_, result, *args):
                try:
                    launcher.launch_finish(result)
                except GLib.GError as e:
                    if e.code != 2: # 'The portal dialog was dismissed by the user' error
                        print("Failed to finish Gtk.FileLauncher procedure.")

            launcher.launch(self, None, open_file_finish)

    def on_switch_toggled(self, switch, active, name):
        self.window_settings.set_setting(name, switch.get_active())
        options = {self.keys[name]: switch.get_active()}
        self.engine.options.update(options)
        self.gl_area.queue_render()

    def on_expander_toggled(self, expander, enabled, name):
        self.window_settings.set_setting(name, expander.get_enable_expansion())
        options = {self.keys[name]: expander.get_enable_expansion()}
        self.engine.options.update(options)
        self.gl_area.queue_render()

    def on_spin_changed(self, spin, value, name):
        val = float(round(spin.get_value(), 2))
        options = {self.keys[name]: val}
        self.window_settings.set_setting(name, val)
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

    def on_color_changed(self, btn, color, setting):
        color_list = rgb_to_list(btn.get_rgba().to_string())
        self.window_settings.set_setting(setting, color_list)
        if setting in self.keys:
            options = {self.keys[setting]: color_list}
            self.engine.options.update(options)
            self.gl_area.queue_render()

    def set_up_direction(self, combo, *args):
        direction = up_dir_n_to_string[combo.get_selected()]
        options = {"scene.up-direction": direction}
        self.engine.options.update(options)
        self.window_settings.set_setting("up-direction", direction)
        print("set up")
        self.load_file(self.filepath, True)

    def set_load_type(self, combo, *args):
        print("set load type")
        load_type = combo.get_selected()
        self.window_settings.set_setting("load-type", load_type)
        self.load_file()

    def update_background_color(self, *args):
        if self.window_settings.get_setting("use-color"):
            options = {
                "render.background.color": self.window_settings.get_setting("background-color"),
            }
            self.engine.options.update(options)
            GLib.idle_add(self.gl_area.queue_render)
            return
        if self.style_manager.get_dark():
            options = {"render.background.color": [0.2, 0.2, 0.2]}
        else:
            options = {"render.background.color": [1.0, 1.0, 1.0]}
        self.engine.options.update(options)
        GLib.idle_add(self.gl_area.queue_render)

    def on_delete_skybox(self, *args):
        self.window_settings.set_setting("skybox-path", "")
        self.window_settings.set_setting("use-skybox", False)
        self.use_skybox_switch.set_active(False)
        options = {"render.hdri.file": "",
                         "render.background.skybox": False}
        self.engine.options.update(options)
        self.gl_area.queue_render()

    def on_open_skybox(self, *args):
        file_filter = Gtk.FileFilter(name="All supported formats")

        for patt in image_patterns:
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

            self.load_hdri(filepath)

    def load_hdri(self, filepath):
        self.window_settings.set_setting("skybox-path", filepath)
        self.window_settings.set_setting("use-skybox", True)
        self.use_skybox_switch.set_active(True)
        self.hdri_file_row.set_filename(filepath)
        options = {"render.hdri.file": filepath,
                         "render.background.skybox": True}
        self.engine.options.update(options)
        self.gl_area.queue_render()

    def set_preference_values(self, block=True):
        if block:
            self.up_direction_combo.handler_block(self.up_direction_combo_handler_id)
            self.model_load_combo.handler_block(self.load_type_combo_handler_id)

        self.grid_switch.set_active(self.window_settings.get_setting("grid"))
        self.absolute_grid_switch.set_active(self.window_settings.get_setting("absolute-grid"))

        self.translucency_switch.set_active(self.window_settings.get_setting("translucency"))
        self.tone_mapping_switch.set_active(self.window_settings.get_setting("tone-mapping"))
        self.ambient_occlusion_switch.set_active(self.window_settings.get_setting("ambient-occlusion"))
        self.anti_aliasing_switch.set_active(self.window_settings.get_setting("anti-aliasing"))
        self.hdri_ambient_switch.set_active(self.window_settings.get_setting("hdri-ambient"))
        self.light_intensity_spin.set_value(self.window_settings.get_setting("light-intensity"))
        self.hdri_file_row.set_filename(self.window_settings.get_setting("skybox-path"))
        self.blur_switch.set_active(self.window_settings.get_setting("blur-background"))
        self.blur_coc_spin.set_value(self.window_settings.get_setting("blur-coc"))
        self.use_skybox_switch.set_active(self.window_settings.get_setting("use-skybox"))

        self.edges_switch.set_active(self.window_settings.get_setting("show-edges"))
        self.edges_width_spin.set_value(self.window_settings.get_setting("edges-width"))

        self.points_expander.set_enable_expansion(self.window_settings.get_setting("show-points"))
        self.points_size_spin.set_value(self.window_settings.get_setting("point-size"))

        self.point_up_switch.set_active(self.window_settings.get_setting("point-up"))
        self.up_direction_combo.set_selected(up_dir_string_to_n[self.window_settings.get_setting("up-direction")])
        self.automatic_up_direction_switch.set_active(self.window_settings.get_setting("auto-up-dir"))

        load_type = self.window_settings.get_setting("load-type")
        self.model_load_combo.set_selected(load_type if load_type else 0)

        self.model_roughness_spin.set_value(self.window_settings.get_setting("model-roughness"))
        self.model_metallic_spin.set_value(self.window_settings.get_setting("model-metallic"))
        rgba = Gdk.RGBA()
        rgba.parse(list_to_rgb(self.window_settings.get_setting("model-color")))
        self.model_color_button.set_rgba(rgba)
        self.model_opacity_spin.set_value(self.window_settings.get_setting("model-opacity"))

        self.use_color_switch.set_active(self.window_settings.get_setting("use-color"))
        rgba = Gdk.RGBA()
        rgba.parse(list_to_rgb(self.window_settings.get_setting("background-color")))
        self.background_color_button.set_rgba(rgba)

        if block:
            self.up_direction_combo.handler_unblock(self.up_direction_combo_handler_id)
            self.model_load_combo.handler_unblock(self.load_type_combo_handler_id)

    def on_restore_settings_clicked(self, btn):
         self.window_settings.load_settings()
         self.set_preference_values(False)

    def on_reset_settings_clicked(self, btn):
        self.window_settings.reset_all()
        self.set_preference_values(False)
        self.gl_area.queue_render()

    def on_save_settings_clicked(self, btn):
        self.window_settings.save_all_settings()

    def create_action(self, name, callback):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        return action

    def generate_thumbnail(self, hdri_file_path, width=300, height=200):
        base_name = os.path.basename(hdri_file_path)
        name, _ = os.path.splitext(base_name)

        thumbnail_name = f"{name}.jpeg"
        thumbnail_filepath = os.path.join(self.hdri_thumbnails_path, thumbnail_name)

        with Image(filename=hdri_file_path) as img:
            img.thumbnail(width, height)
            img.gamma(1.7)
            img.brightness_contrast(0, -5)
            img.format = 'jpeg'
            img.save(filename=thumbnail_filepath)

        return thumbnail_filepath

def p_dist(point1, point2):
    if len(point1) != len(point2):
        raise ValueError("Points must have the same dimension")

    squared_diffs = [(x - y) ** 2 for x, y in zip(point1, point2)]
    return math.sqrt(sum(squared_diffs))

def v_mod(vector):
    return math.sqrt(sum([(x) ** 2 for x in vector]))

def v_abs(vector):
    return tuple(abs(x) for x in vector)

def v_norm(vector):
    norm = math.sqrt(sum(x**2 for x in vector))
    return tuple(x / norm for x in vector)

def v_add(vector1, vector2):
    return tuple(v1 + v2 for v1, v2 in zip(vector1, vector2))

def v_sub(vector1, vector2):
    return tuple(v1 - v2 for v1, v2 in zip(vector1, vector2))

def v_mul(vector, scalar):
    return tuple(v * scalar for v in vector)

def v_dot_p(vector1, vector2):
    return tuple(v1 * v2 for v1, v2 in zip(vector1, vector2))

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

def get_up_from_path(path):
    extension = os.path.splitext(path)[1][1:]
    up_ext = {
        "stl" : "+Z",
        "3ds" : "+Z",
        "obj" : "+Z",
        "ply" : "+Z"
    }
    if extension in up_ext:
        return up_ext[extension]
    return "+Y"

def list_files(directory):
    items = os.listdir(directory)
    files = [item for item in items if os.path.isfile(os.path.join(directory, item))]
    return files
