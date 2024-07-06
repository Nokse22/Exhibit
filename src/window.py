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
from .vector_math import *

import f3d
from f3d import *

import math
import os
import threading
import datetime
import json

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
            "grid": True,
            "absolute-grid": False,
            "translucency-support": True,
            "tone-mapping": False,
            "ambient-occlusion": False,
            "anti-aliasing": True,
            "hdri-ambient": False,
            "light-intensity": 1.0,
            "orthographic": False,
            "point-up": True,
            "hdri-file": "",
            "blur-background": True,
            "blur-coc": 20.0,
            "use-skybox": False,
            "background-color": (1.0, 1.0, 1.0),
            "use-color": False,
            "show-edges": False,
            "edges-width": 1.0,
            "up": "-Y",
            "auto-up-dir" : True,
            "show-points": False,
            "point-size": 1.0,
            "model-color": (1.0, 1.0, 1.0),
            "model-metallic": 0.0,
            "model-roughness": 0.3,
            "model-opacity": 1.0,
            "load-type": None, # 0 for geometry and 1 for scene
            "comp": 0,
        }

    def set_setting(self, key, val):
        self.settings[key] = val

    def get_setting(self, key):
        return self.settings[key]

    def save_all_settings(self):
        pass

    def reset_all(self):
        for key in self.settings:
            self.saved_settings.reset(key)
        self.load_settings()
        self.save_all_settings()

@Gtk.Template(resource_path='/io/github/nokse22/Exhibit/ui/window.ui')
class Viewer3dWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'Viewer3dWindow'

    split_view = Gtk.Template.Child()

    f3d_viewer = Gtk.Template.Child()

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
    spheres_switch = Gtk.Template.Child()
    points_size_spin = Gtk.Template.Child()

    model_load_combo = Gtk.Template.Child()

    material_group = Gtk.Template.Child()

    model_roughness_spin = Gtk.Template.Child()
    model_metallic_spin = Gtk.Template.Child()
    model_color_button = Gtk.Template.Child()
    model_opacity_spin = Gtk.Template.Child()

    model_color_row = Gtk.Template.Child()
    model_scivis_component_combo = Gtk.Template.Child()
    color_group = Gtk.Template.Child()

    startup_stack = Gtk.Template.Child()

    settings_section= Gtk.Template.Child()

    width = 600
    height = 600
    distance = 0

    file_name = ""

    def __init__(self, application=None, startup_filepath=None):
        super().__init__(application=application)

        self.save_as_action = self.create_action('save-as-image', self.open_save_file_chooser)
        self.open_new_action = self.create_action('open-new', self.open_file_chooser)

        self.settings_action = Gio.SimpleAction.new_stateful(
            "settings",
            GLib.VariantType.new("s"),
            GLib.Variant("s", "general"),
        )
        self.settings_action.connect("activate", self.on_settings_changed)
        self.add_action(self.settings_action)

        self.save_settings_action = self.create_action('save-settings', self.on_save_settings)
        self.save_settings_action.set_enabled(False)

        self.configurations = Gio.resources_lookup_data('/io/github/nokse22/Exhibit/configurations.json', Gio.ResourceLookupFlags.NONE).get_data().decode('utf-8')
        self.configurations = json.loads(self.configurations)

        item = Gio.MenuItem.new("Custom", "win.settings")
        item.set_attribute_value("target", GLib.Variant.new_string("custom"))
        self.settings_section.append_item(item)

        for key, setting in self.configurations.items():
            item = Gio.MenuItem.new(setting["name"], "win.settings")
            item.set_attribute_value("target", GLib.Variant.new_string(key))
            self.settings_section.append_item(item)

        self.view_drop_target.set_gtypes([Gdk.FileList])
        self.loading_drop_target.set_gtypes([Gdk.FileList])

        self.window_settings = WindowSettings()
        settings = Gio.Settings.new('io.github.nokse22.Exhibit')

        self.set_default_size(settings.get_int("startup-width"), settings.get_int("startup-height"))
        self.split_view.set_show_sidebar(settings.get_boolean("startup-sidebar-show"))

        self.set_preference_values(False)

        self.grid_switch.connect("notify::active", self.on_switch_toggled, "grid")
        self.absolute_grid_switch.connect("notify::active", self.on_switch_toggled, "absolute-grid")

        self.translucency_switch.connect("notify::active", self.on_switch_toggled, "translucency-support")
        self.tone_mapping_switch.connect("notify::active", self.on_switch_toggled, "tone-mapping")
        self.ambient_occlusion_switch.connect("notify::active", self.on_switch_toggled, "ambient-occlusion")
        self.anti_aliasing_switch.connect("notify::active", self.on_switch_toggled, "anti-aliasing")
        self.hdri_ambient_switch.connect("notify::active", self.on_switch_toggled, "hdri-ambient")

        self.edges_switch.connect("notify::active", self.on_switch_toggled, "show-edges")
        self.edges_width_spin.connect("notify::value", self.on_spin_changed, "edges-width")

        self.spheres_switch.connect("notify::active", self.on_switch_toggled, "show-points")
        self.points_size_spin.connect("notify::value", self.on_spin_changed, "point-size")

        self.load_type_combo_handler_id = self.model_load_combo.connect("notify::selected", self.set_load_type)
        self.model_roughness_spin.connect("notify::value", self.on_spin_changed, "model-roughness")
        self.model_metallic_spin.connect("notify::value", self.on_spin_changed, "model-metallic")
        self.model_color_button.connect("notify::rgba", self.on_color_changed, "model-color")
        self.model_opacity_spin.connect("notify::value", self.on_spin_changed, "model-opacity")
        self.model_scivis_component_combo.connect("notify::selected", self.on_scivis_component_combo_changed)

        self.light_intensity_spin.connect("notify::value", self.on_spin_changed, "light-intensity")

        self.use_skybox_switch.connect("notify::active", self.on_switch_toggled, "hdri-skybox")

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

        if self.window_settings.get_setting("orthographic"):
            self.toggle_orthographic()

        self.no_file_loaded = True

        self.style_manager = Adw.StyleManager().get_default()
        self.style_manager.connect("notify::dark", self.update_background_color)

        self.update_background_color()

        if startup_filepath:
            print("start file")
            self.load_file(startup_filepath)

    def on_settings_changed(self, action: Gio.SimpleAction, state: GLib.Variant):
        self.settings_action.set_state(state)

        options = {}
        for key, value in self.configurations[state.get_string()]["settings"].items():
            options[key] = value

        self.f3d_viewer.update_options(options)
        self.f3d_viewer.reset_to_bounds()

        if state == GLib.Variant("s", "custom"):
            self.save_settings_action.set_enabled(True)
        else:
            self.save_settings_action.set_enabled(False)

    def on_save_settings(self, *args):
        print("saving settings")

    def get_gimble_limit(self):
        return self.distance / 10

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
            self.window_settings.set_setting("up", up)

        options = {"scene.up-direction": self.window_settings.get_setting("up")}
        self.f3d_viewer.update_options(options)
        self.settings_action.set_state(GLib.Variant("s", "custom"))

        def _load():
            scene_loaded = False
            geometry_loaded = False

            if self.window_settings.get_setting("load-type") is None:
                if self.f3d_viewer.has_scene_loader(filepath):
                    self.f3d_viewer.load_scene(filepath)
                    scene_loaded = True
                    GLib.idle_add(self.model_load_combo.set_sensitive, True)
                elif self.f3d_viewer.has_geometry_loader(filepath):
                    self.f3d_viewer.load_geometry(filepath)
                    geometry_loaded = True
                    GLib.idle_add(self.model_load_combo.set_sensitive, False)

            elif self.window_settings.get_setting("load-type") == 0:
                if self.f3d_viewer.has_geometry_loader(filepath):
                    self.f3d_viewer.load_geometry(filepath)
                    geometry_loaded = True
            elif self.window_settings.get_setting("load-type") == 1:
                if self.f3d_viewer.has_scene_loader(filepath):
                    self.f3d_viewer.load_scene(filepath)
                    scene_loaded = True

            if not scene_loaded and not geometry_loaded:
                GLib.idle_add(self.on_file_not_opened, filepath)
                return

            if self.f3d_viewer.has_geometry_loader(filepath) and self.f3d_viewer.has_scene_loader(filepath):
                GLib.idle_add(self.model_load_combo.set_sensitive, True)
            else:
                GLib.idle_add(self.model_load_combo.set_sensitive, False)

            if scene_loaded:
                self.window_settings.set_setting("load-type", 1)
            elif geometry_loaded:
                self.window_settings.set_setting("load-type", 0)

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
            self.color_group.set_sensitive(True)
        elif self.window_settings.get_setting("load-type") == 1:
            self.material_group.set_sensitive(False)
            self.points_group.set_sensitive(False)
            self.color_group.set_sensitive(False)
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
        options = {"scene.up-direction": self.window_settings.get_setting("up")}
        self.f3d_viewer.update_options(options)
        self.settings_action.set_state(GLib.Variant("s", "custom"))

    def send_toast(self, message):
        toast = Adw.Toast(title=message, timeout=2)
        self.toast_overlay.add_toast(toast)

    def update_options(self):
        options = {}
        for key, value in self.window_settings.settings.items():
            options[key] = value

        self.f3d_viewer.update_options(options)
        self.settings_action.set_state(GLib.Variant("s", "custom"))
        self.update_background_color()

    def save_as_image(self, filepath):
        img = self.f3d_viewer.render_image()
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

    @Gtk.Template.Callback("on_home_clicked")
    def on_home_clicked(self, btn):
        self.f3d_viewer.reset_to_bounds()

    @Gtk.Template.Callback("on_open_button_clicked")
    def on_open_button_clicked(self, btn):
        self.open_file_chooser()

    @Gtk.Template.Callback("on_view_clicked")
    def toggle_orthographic(self, *args):
        btn = self.view_button_headerbar
        if (btn.get_icon_name() == "perspective-symbolic"):
            btn.set_icon_name("orthographic-symbolic")
            camera_options = {"orthographic": True}
            self.window_settings.set_setting("orthographic", True)
        else:
            btn.set_icon_name("perspective-symbolic")
            camera_options = {"orthographic": False}
            self.window_settings.set_setting("orthographic", False)
        self.f3d_viewer.update_options(camera_options)

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
            launcher.set_always_ask(True)

            def open_file_finish(_, result, *args):
                try:
                    launcher.launch_finish(result)
                except GLib.GError as e:
                    if e.code != 2: # 'The portal dialog was dismissed by the user' error
                        print("Failed to finish Gtk.FileLauncher procedure.")

            launcher.launch(self, None, open_file_finish)

    def on_switch_toggled(self, switch, active, name):
        self.window_settings.set_setting(name, switch.get_active())
        options = {name: switch.get_active()}
        self.f3d_viewer.update_options(options)
        self.settings_action.set_state(GLib.Variant("s", "custom"))

    def on_expander_toggled(self, expander, enabled, name):
        self.window_settings.set_setting(name, expander.get_enable_expansion())
        options = {name: expander.get_enable_expansion()}
        self.f3d_viewer.update_options(options)
        self.settings_action.set_state(GLib.Variant("s", "custom"))

    def on_spin_changed(self, spin, value, name):
        val = float(round(spin.get_value(), 2))
        options = {name: val}
        self.window_settings.set_setting(name, val)
        self.f3d_viewer.update_options(options)
        self.settings_action.set_state(GLib.Variant("s", "custom"))

    def set_point_up(self, switch, active, name):
        val = switch.get_active()
        self.window_settings.set_setting(name, val)
        if val:
            self.f3d_viewer.set_view_up(up_dirs_vector[self.window_settings.get_setting("up")])
            self.f3d_viewer.always_point_up = True
        else:
            self.f3d_viewer.always_point_up = False

    def on_color_changed(self, btn, color, setting):
        color_list = rgb_to_list(btn.get_rgba().to_string())
        self.window_settings.set_setting(setting, color_list)
        options = {setting: color_list}
        self.f3d_viewer.update_options(options)
        self.settings_action.set_state(GLib.Variant("s", "custom"))

    def set_up_direction(self, combo, *args):
        direction = up_dir_n_to_string[combo.get_selected()]
        options = {"scene.up-direction": direction}
        self.f3d_viewer.update_options(options)
        self.settings_action.set_state(GLib.Variant("s", "custom"))
        self.window_settings.set_setting("up", direction)
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
                "background-color": self.window_settings.get_setting("background-color"),
            }
            self.f3d_viewer.update_options(options)
            self.settings_action.set_state(GLib.Variant("s", "custom"))
            GLib.idle_add(self.f3d_viewer.queue_render)
            return
        if self.style_manager.get_dark():
            options = {"background-color": [0.2, 0.2, 0.2]}
        else:
            options = {"background-color": [1.0, 1.0, 1.0]}
        self.f3d_viewer.update_options(options)
        self.settings_action.set_state(GLib.Variant("s", "custom"))
        GLib.idle_add(self.f3d_viewer.queue_render)

    def on_scivis_component_combo_changed(self, combo, *args):
        selected = combo.get_selected()
        self.model_color_row.set_sensitive(True if selected == 0 else False)

        self.window_settings.set_setting("comp", -selected)
        if selected == 0:
            options = {
                "comp": -1,
                "cells": True
            }
        else:
            options = {
                "comp": - (selected - 1),
                "cells": False
            }
        self.f3d_viewer.update_options(options)
        self.settings_action.set_state(GLib.Variant("s", "custom"))

    def on_delete_skybox(self, *args):
        self.window_settings.set_setting("hdri-file", "")
        self.window_settings.set_setting("use-skybox", False)
        self.use_skybox_switch.set_active(False)
        options = {"hdri-file": "",
                         "hdri-skybox": False}
        self.f3d_viewer.update_options(options)
        self.settings_action.set_state(GLib.Variant("s", "custom"))

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
        self.window_settings.set_setting("hdri-file", filepath)
        self.window_settings.set_setting("use-skybox", True)
        self.use_skybox_switch.set_active(True)
        self.hdri_file_row.set_filename(filepath)
        options = {"hdri-file": filepath,
                         "hdri-skybox": True}
        self.f3d_viewer.update_options(options)
        self.settings_action.set_state(GLib.Variant("s", "custom"))

    def set_preference_values(self, block=True):
        if block:
            self.up_direction_combo.handler_block(self.up_direction_combo_handler_id)
            self.model_load_combo.handler_block(self.load_type_combo_handler_id)

        self.grid_switch.set_active(self.window_settings.get_setting("grid"))
        self.absolute_grid_switch.set_active(self.window_settings.get_setting("absolute-grid"))

        self.translucency_switch.set_active(self.window_settings.get_setting("translucency-support"))
        self.tone_mapping_switch.set_active(self.window_settings.get_setting("tone-mapping"))
        self.ambient_occlusion_switch.set_active(self.window_settings.get_setting("ambient-occlusion"))
        self.anti_aliasing_switch.set_active(self.window_settings.get_setting("anti-aliasing"))
        self.hdri_ambient_switch.set_active(self.window_settings.get_setting("hdri-ambient"))
        self.light_intensity_spin.set_value(self.window_settings.get_setting("light-intensity"))
        self.hdri_file_row.set_filename(self.window_settings.get_setting("hdri-file"))
        self.blur_switch.set_active(self.window_settings.get_setting("blur-background"))
        self.blur_coc_spin.set_value(self.window_settings.get_setting("blur-coc"))
        self.use_skybox_switch.set_active(self.window_settings.get_setting("use-skybox"))

        self.edges_switch.set_active(self.window_settings.get_setting("show-edges"))
        self.edges_width_spin.set_value(self.window_settings.get_setting("edges-width"))

        self.spheres_switch.set_active(self.window_settings.get_setting("show-points"))
        self.points_size_spin.set_value(self.window_settings.get_setting("point-size"))

        self.point_up_switch.set_active(self.window_settings.get_setting("point-up"))
        self.up_direction_combo.set_selected(up_dir_string_to_n[self.window_settings.get_setting("up")])
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
        self.f3d_viewer.queue_render()

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
