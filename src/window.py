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

import os
import json
import re
import threading

from gi.repository import Adw, Gtk, Gdk, Gio, GLib, GObject
from .widgets import F3DViewer, FileRow
from wand.image import Image

from . import logger_lib
from .settings_manager import WindowSettings

from gettext import gettext as _

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

file_patterns = [
    "*.vtk", "*.vtp", "*.vtu", "*.vtr", "*.vti", "*.vts", "*.vtm", "*.ply",
    "*.stl", "*.dcm", "*.drc", "*.nrrd", "*.nhrd", "*.mhd", "*.mha", "*.ex2",
    "*.e", "*.exo", "*.g", "*.gml", "*.pts", "*.splat", "*.ply", "*.step",
    "*.stp", "*.iges", "*.igs", "*.brep", "*.abc", "*.obj", "*.gltf", "*.glb",
    "*.3ds", "*.wrl", "*.fbx", "*.dae", "*.off", "*.dxf", "*.x", "*.3mf",
    "*.usd", "*.usda", "*.usdc", "*.usdz"
]

allowed_extensions = [pattern.lstrip('*.') for pattern in file_patterns]

image_patterns = [
    "*.hdr", "*.exr", "*.png", "*.jpg", "*.pnm", "*.tiff", "*.bmp"
]


class PeriodicChecker(GObject.Object):
    def __init__(self, function):
        super().__init__()

        self._running = False
        self._function = function

    def run(self):
        if self._running:
            return
        self._running = True
        GLib.timeout_add(500, self.periodic_check)

    def stop(self):
        self._running = False

    def periodic_check(self):
        if self._running:
            self._function()
            return True
        else:
            return False


@Gtk.Template(resource_path='/io/github/nokse22/Exhibit/ui/window.ui')
class Viewer3dWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'Viewer3dWindow'

    loading_label = Gtk.Template.Child()

    split_view = Gtk.Template.Child()

    f3d_viewer = Gtk.Template.Child()

    title_widget = Gtk.Template.Child()
    stack = Gtk.Template.Child()
    toolbar_view = Gtk.Template.Child()

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

    automatic_settings_switch = Gtk.Template.Child()

    automatic_reload_switch = Gtk.Template.Child()

    points_group = Gtk.Template.Child()
    spheres_switch = Gtk.Template.Child()
    points_size_spin = Gtk.Template.Child()
    point_sprites_type_combo = Gtk.Template.Child()

    material_group = Gtk.Template.Child()

    model_roughness_spin = Gtk.Template.Child()
    model_metallic_spin = Gtk.Template.Child()
    model_color_button = Gtk.Template.Child()
    model_opacity_spin = Gtk.Template.Child()

    armature_switch = Gtk.Template.Child()

    model_color_row = Gtk.Template.Child()
    model_scivis_component_combo = Gtk.Template.Child()
    color_group = Gtk.Template.Child()

    startup_stack = Gtk.Template.Child()

    settings_section = Gtk.Template.Child()

    save_dialog = Gtk.Template.Child()
    settings_column_view = Gtk.Template.Child()
    settings_column_view_name_column = Gtk.Template.Child()
    settings_column_view_value_column = Gtk.Template.Child()
    save_settings_button = Gtk.Template.Child()
    save_settings_name_entry = Gtk.Template.Child()
    save_settings_extensions_entry = Gtk.Template.Child()
    save_settings_expander = Gtk.Template.Child()

    animation_group = Gtk.Template.Child()
    animation_time_adj = Gtk.Template.Child()
    animation_index_adj = Gtk.Template.Child()
    play_button = Gtk.Template.Child()

    width = 600
    height = 600
    distance = 0

    file_name = ""
    filepath = ""
    no_file_loaded = True

    _cached_time_stamp = 0

    def __init__(self, application=None, startup_filepath=None):
        super().__init__(application=application)

        self.logger = logger_lib.logger

        # Flags
        self.applying_breakpoint = False
        self.block_reload = True

        # Settings
        self.window_settings = WindowSettings()
        self.saved_settings = Gio.Settings.new('io.github.nokse22.Exhibit')

        # Defining all the actions
        self.save_as_action = self.create_action(
            'save-as-image', self.open_save_file_chooser)
        self.open_new_action = self.create_action(
            'open-new', self.open_file_chooser)
        self.open_new_action = self.create_action(
            'add-new', self.open_file_chooser)

        self.orthonographic_action = Gio.SimpleAction.new_stateful(
            "orthonographic",
            GLib.VariantType.new("b"),
            GLib.Variant(
                "b",
                self.window_settings.get_setting("orthographic")),
        )
        self.orthonographic_action.connect(
            "change-state",
            lambda action, state: self.orthonographic_state_changed(state))
        self.add_action(self.orthonographic_action)

        self.settings_action = Gio.SimpleAction.new_stateful(
            "settings",
            GLib.VariantType.new("s"),
            GLib.Variant("s", "general"),
        )
        self.settings_action.connect(
            "change-state",
            lambda action, state: self.change_setting_state(state))
        self.add_action(self.settings_action)

        self.save_settings_action = self.create_action(
            'save-settings', self.on_save_settings)
        self.save_settings_action.set_enabled(False)

        # Initialize the change checker
        self.change_checker = PeriodicChecker(
            self.periodic_check_for_file_change)

        # Saving all the useful paths
        data_home = os.environ["XDG_DATA_HOME"]

        self.hdri_path = data_home + "/HDRIs/"
        self.hdri_thumbnails_path = self.hdri_path + "/thumbnails/"

        self.user_configurations_path = data_home + "/configurations/"

        os.makedirs(self.user_configurations_path, exist_ok=True)
        os.makedirs(data_home + "/other files/", exist_ok=True)

        # Create the hdri folder and add the default if there are none
        self.setup_hdri_folder()

        # Loading the saved configurations
        self.setup_configurations()

        # Setting drop target type
        self.view_drop_target.set_gtypes([Gdk.FileList])
        self.loading_drop_target.set_gtypes([Gdk.FileList])

        # Setting the window to the last state
        self.set_default_size(
            self.saved_settings.get_int("startup-width"),
            self.saved_settings.get_int("startup-height")
        )
        self.split_view.set_show_sidebar(
            self.saved_settings.get_boolean("startup-sidebar-show"))
        self.window_settings.set_setting(
            "sidebar-show",
            self.saved_settings.get_boolean("startup-sidebar-show"))

        # Getting the saved HDRI and generating thumbnails
        self.hdri_file_row.file_patterns = image_patterns
        self.hdri_file_row.window = self

        for filename in list_files(self.hdri_path):
            name, _ = os.path.splitext(filename)

            thumbnail = self.hdri_thumbnails_path + name + ".jpeg"
            filepath = self.hdri_path + filename
            try:
                if not os.path.isfile(thumbnail):
                    thumbnail = self.generate_thumbnail(filepath)
                self.hdri_file_row.add_suggested_file(thumbnail, filepath)
            except Exception:
                self.logger.warning(
                    f"Couldn't open HDRI file {filepath}, skipping")

        self.style_manager = Adw.StyleManager().get_default()
        self.style_manager.connect(
            "notify::dark", self.update_background_color)

        self.update_background_color()

        # Setting up the save settings dialog
        def _on_factory_setup(_factory, list_item):
            label = Gtk.Label(xalign=0, ellipsize=3)
            list_item.set_child(label)

        def _on_factory_bind(_factory, list_item, what):
            label_widget = list_item.get_child()
            setting = list_item.get_item()
            label_widget.set_label(str(getattr(setting, what)))

        self.settings_column_view_name_column.get_factory().connect(
            "setup", _on_factory_setup)
        self.settings_column_view_name_column.get_factory().connect(
            "bind", _on_factory_bind, "name")
        self.settings_column_view_value_column.get_factory().connect(
            "setup", _on_factory_setup)
        self.settings_column_view_value_column.get_factory().connect(
            "bind", _on_factory_bind, "value")

        selection = Gtk.NoSelection.new(model=self.window_settings)
        self.settings_column_view.set_model(model=selection)

        self.save_settings_button.connect(
            "clicked", self.on_save_settings_button_clicked)
        self.save_settings_name_entry.connect(
            "changed", self.on_save_settings_name_entry_changed)
        self.save_settings_extensions_entry.connect(
            "changed", self.on_save_settings_extensions_entry_changed)

        # Setting the UI and connecting widgets
        self.window_settings.connect(
            "changed-other", self.on_other_setting_changed)
        self.window_settings.connect(
            "changed-internal", self.on_internal_setting_changed)
        self.window_settings.connect(
            "changed-view", self.on_view_setting_changed)

        # Switches signals
        switches = [
            (self.grid_switch, "grid"),
            (self.absolute_grid_switch, "grid-absolute"),
            (self.translucency_switch, "translucency-support"),
            (self.tone_mapping_switch, "tone-mapping"),
            (self.ambient_occlusion_switch, "ambient-occlusion"),
            (self.anti_aliasing_switch, "anti-aliasing"),
            (self.hdri_ambient_switch, "hdri-ambient"),
            (self.edges_switch, "show-edges"),
            (self.spheres_switch, "point-sprites"),
            (self.use_skybox_switch, "hdri-skybox"),
            (self.blur_switch, "blur-background"),
            (self.use_color_switch, "use-color"),
            (self.automatic_settings_switch, "auto-best"),
            (self.automatic_reload_switch, "auto-reload"),
            (self.point_up_switch, "point-up"),
            (self.armature_switch, "armature-enable")
        ]

        for switch, name in switches:
            switch.connect("notify::active", self.on_switch_toggled, name)
            setting = self.window_settings.get_setting(name)
            setting.connect("changed", self.set_switch_to, switch)

        # Spins
        spins = [
            (self.edges_width_spin, "edges-width"),
            (self.points_size_spin, "point-size"),
            (self.model_roughness_spin, "model-roughness"),
            (self.model_metallic_spin, "model-metallic"),
            (self.model_opacity_spin, "model-opacity"),
            (self.blur_coc_spin, "blur-coc"),
            (self.light_intensity_spin, "light-intensity"),
        ]

        for spin, name in spins:
            spin.connect("notify::value", self.on_spin_changed, name)
            setting = self.window_settings.get_setting(name)
            setting.connect("changed", self.set_spin_to, spin)

        # Color buttons
        self.model_color_button.connect(
            "notify::rgba", self.on_color_changed, "model-color")
        self.background_color_button.connect(
            "notify::rgba", self.on_color_changed, "bg-color")
        self.window_settings.get_setting("model-color").connect(
            "changed", self.set_color_button, self.model_color_button)
        self.window_settings.get_setting("bg-color").connect(
            "changed", self.set_color_button, self.background_color_button)

        # File rows
        self.hdri_file_row.connect(
            "delete-file", self.on_delete_skybox)
        self.hdri_file_row.connect(
            "file-added", lambda row, filepath: self.load_hdri(filepath))
        self.window_settings.get_setting("hdri-file").connect(
            "changed", self.set_hdri_file_row)

        # Combos
        self.model_scivis_component_combo.connect(
            "notify::selected", self.on_scivis_component_combo_changed)
        self.window_settings.get_setting("up").connect(
            "changed", self.set_up_direction_combo)
        self.window_settings.get_setting("comp").connect(
            "changed", self.set_scivis_component_combo)
        self.window_settings.get_setting("cells").connect(
            "changed", self.set_scivis_component_combo)
        self.point_sprites_type_combo.connect(
            "notify::selected", self.point_sprites_type_combo_changed)
        self.window_settings.get_setting("point-type").connect(
            "changed", self.set_point_sprites_type_combo_changed)

        # Others
        self.background_color_button.connect(
            "notify::rgba", self.update_background_color)

        self.up_direction_combo.connect(
            "notify::selected", self.on_up_direction_combo_changed)

        self.window_settings.set_setting(
            "auto-best", self.saved_settings.get_boolean("auto-best"))

        self.animation_time_adj.bind_property(
            "lower", self.f3d_viewer, "lower-time-range", 1)
        self.animation_time_adj.bind_property(
            "upper", self.f3d_viewer, "upper-time-range", 1)
        self.animation_time_adj.bind_property(
            "value", self.f3d_viewer, "animation-time", 3)

        self.play_button.connect("clicked", self.on_play_button_clicked)

        self.f3d_viewer.connect("notify::playing", self.on_playing_changed)

        self.animation_index_adj.connect(
            "value-changed", self.on_animation_index_changed)

        self.block_reload = True

        # Sync the UI with the settings
        self.window_settings.sync_all_settings()

        self.block_reload = False

        if startup_filepath:
            self.logger.info(f"startup file detected: {startup_filepath}")
            self.load_file(filepath=startup_filepath)

        self.logger.info("Started")

    def setup_configurations(self):
        self.configurations = Gio.resources_lookup_data(
            '/io/github/nokse22/Exhibit/configurations.json',
            Gio.ResourceLookupFlags.NONE).get_data().decode('utf-8')
        self.configurations = json.loads(self.configurations)

        for filename in os.listdir(self.user_configurations_path):
            if filename.endswith('.json'):
                filepath = os.path.join(
                    self.user_configurations_path, filename)
                with open(filepath, 'r') as file:
                    try:
                        configuration = json.load(file)

                        # Check if the loaded configurations
                        #   has all the required keys
                        required_keys = {
                            "name", "formats",
                            "view-settings", "other-settings"
                        }
                        first_key_value = next(iter(configuration.values()))
                        if required_keys.issubset(first_key_value.keys()):
                            self.configurations.update(configuration)
                        else:
                            self.logger.error(
                                f"Error: {filepath} is missing required keys.")

                    except json.JSONDecodeError as e:
                        self.logger.error(f"Error reading {filename}: {e}")

        item = Gio.MenuItem.new("Custom", "win.settings")
        item.set_attribute_value("target", GLib.Variant.new_string("custom"))
        self.settings_section.append_item(item)

        for key, setting in self.configurations.items():
            item = Gio.MenuItem.new(setting["name"], "win.settings")
            item.set_attribute_value("target", GLib.Variant.new_string(key))
            self.settings_section.append_item(item)

    def setup_hdri_folder(self):
        if not os.path.isdir(self.hdri_path):
            return

        os.makedirs(self.hdri_path, exist_ok=True)
        os.makedirs(self.hdri_thumbnails_path, exist_ok=True)

        hdri_names = ["city.hdr", "meadow.hdr", "field.hdr", "sky.hdr"]
        for hdri_filename in hdri_names:
            if not os.path.isfile(self.hdri_path + hdri_filename):
                hdri = Gio.resources_lookup_data(
                    '/io/github/nokse22/Exhibit/HDRIs/' + hdri_filename,
                    Gio.ResourceLookupFlags.NONE).get_data()
                hdri_bytes = bytearray(hdri)
                with open(self.hdri_path + hdri_filename, 'wb') as output_file:
                    output_file.write(hdri_bytes)
                self.logger.info(f"Added {hdri_filename}")

    #
    # Functions that set the UI from the settings, triggered when
    #   a setting has changed.

    def set_hdri_file_row(self, setting, name, enum):
        self.logger.info(f"Setting hdri file row filename to {setting.value}")
        self.hdri_file_row.set_filename(setting.value)

    def set_switch_to(self, setting, name, enum, switch):
        self.logger.info(f"Setting switch to {setting.value}")
        switch.set_active(setting.value)

    def set_spin_to(self, setting, name, enum, spin):
        self.logger.info(f"Setting spin to {setting.value}")
        spin.set_value(setting.value)

    def set_up_direction_combo(self, *args):
        val = up_dir_string_to_n[self.window_settings.get_setting("up").value]
        self.logger.info(f"Setting up direction combo to {val}")
        self.up_direction_combo.set_selected(val)

    def set_color_button(self, setting, name, enum, color_button):
        rgba = Gdk.RGBA()
        rgba.parse(list_to_rgb(setting.value))
        color_button.set_rgba(rgba)

    def set_scivis_component_combo(self, setting, *args):
        selected = self.model_scivis_component_combo.get_selected()
        self.logger.debug(
            f"Setting scivis component combo, selected: {selected}")
        self.model_color_row.set_sensitive(True if selected == 0 else False)

        if (self.window_settings.get_setting("comp").value == -1 and
                self.window_settings.get_setting("cells").value):
            self.model_scivis_component_combo.set_selected(0)
        else:
            self.model_scivis_component_combo.set_selected(
                -self.window_settings.get_setting("comp").value + 1)

    def set_point_sprites_type_combo_changed(self, setting, *args):
        if self.window_settings.get_setting("comp").value == "spheres":
            self.point_sprites_type_combo.set_selected(0)
        else:
            self.point_sprites_type_combo.set_selected(1)

    # Functions that are called when a UI changes, they should only
    #   set the corresponding setting.

    def on_animation_index_changed(self, *args):
        self.f3d_viewer.update_options(
            {"animation-index": int(self.animation_index_adj.get_value())})
        self.f3d_viewer.animation_time = self.f3d_viewer.lower_time_range
        self.f3d_viewer.playing = False

        self.reload_file(True)

    def on_switch_toggled(self, switch, active, name):
        self.window_settings.set_setting(name, switch.get_active())

    def on_expander_toggled(self, expander, enabled, name):
        self.window_settings.set_setting(name, expander.get_enable_expansion())

    def on_spin_changed(self, spin, value, name):
        val = float(round(spin.get_value(), 2))
        self.window_settings.set_setting(name, val)

    def on_color_changed(self, btn, color, setting):
        color_list = rgb_to_list(btn.get_rgba().to_string())
        self.window_settings.set_setting(setting, color_list)

    def on_up_direction_combo_changed(self, combo, *args):
        direction = up_dir_n_to_string[combo.get_selected()]
        self.window_settings.set_setting("up", direction)

    def on_scivis_component_combo_changed(self, *args):
        selected = self.model_scivis_component_combo.get_selected()
        self.model_color_row.set_sensitive(True if selected == 0 else False)

        if selected == 0:
            self.window_settings.set_setting("comp", -1, False)
            self.window_settings.set_setting("cells", True)
            self.window_settings.set_setting("scalar-coloring", False)
        else:
            self.window_settings.set_setting("comp", -(selected - 1))
            self.window_settings.set_setting("cells", False)
            self.window_settings.set_setting("scalar-coloring", True)

    def point_sprites_type_combo_changed(self, *args):
        selected = self.point_sprites_type_combo.get_selected()

        if selected == 0:
            self.window_settings.set_setting("point-type", "sphere", False)
        else:
            self.window_settings.set_setting("point-type", "gaussian", False)
    #
    # Special functions called when a setting changes that trigger
    #   an action like reloading.

    def reload_file(self, pres_or=False):
        if not self.block_reload:
            self.logger.info("Reloading file")
            self.load_file(
                filepath=self.filepath,
                override=True,
                preserve_orientation=pres_or)

    def update_background_color(self, *args):
        self.logger.info(
            f"Use color is: {self.window_settings.get_setting('use-color').value}")
        if self.window_settings.get_setting("use-color").value:
            options = {
                "bg-color": self.window_settings.get_setting("bg-color").value,
            }
            self.f3d_viewer.update_options(options)
            GLib.idle_add(self.f3d_viewer.queue_render)
            return
        if self.style_manager.get_dark():
            options = {"bg-color": [0.117, 0.117, 0.117]}
        else:
            options = {"bg-color": [1.0, 1.0, 1.0]}
        self.f3d_viewer.update_options(options)
        GLib.idle_add(self.f3d_viewer.queue_render)

    # Functions to set the settings

    def on_view_setting_changed(self, window_settings, setting):
        self.logger.info(f"Setting: {setting.name} to {setting.value}")
        options = {setting.name: setting.value}
        self.f3d_viewer.update_options(options)
        self.check_for_options_change()

        if setting.name == "up":
            self.reload_file()

    def on_other_setting_changed(self, window_settings, setting):
        self.logger.info(f"Setting: {setting.name} to {setting.value}")
        if setting.name == "use-color":
            self.update_background_color()
        elif setting.name == "point-up":
            if setting.value:
                self.f3d_viewer.set_view_up(
                    up_dirs_vector[
                        self.window_settings.get_setting("up").value])
                self.f3d_viewer.always_point_up = True
            else:
                self.f3d_viewer.always_point_up = False
        elif setting.name == "auto-reload":
            if setting.value:
                self.change_checker.run()
            else:
                self.change_checker.stop()

        self.check_for_options_change()

    def on_internal_setting_changed(self, window_settings, setting):
        self.logger.info(f"Setting: {setting.name} to {setting.value}")
        if setting.name == "auto-best":
            pass
        elif setting.name == "sidebar-show":
            pass

    # Functions related to the save settings dialog

    def on_save_settings_button_clicked(self, btn):
        # Extract view settings, name, and formats
        view_settings = self.window_settings.get_view_settings()
        other_settings = self.window_settings.get_other_settings()
        name = self.save_settings_name_entry.get_text()
        formats = self.save_settings_extensions_entry.get_text()

        # Format the key
        key = name.lower().replace(' ', '_')

        # Construct the dictionary
        settings_dict = {
            key: {
                "name": name,
                "formats": f".*({formats.replace(', ', '|')})",
                "view-settings": view_settings,
                "other-settings": other_settings
            }
        }

        # Save to JSON file
        with open(self.user_configurations_path + key + '.json', 'w') as j_f:
            json.dump(settings_dict, j_f, indent=4)

        # Update configurations and menu UI
        self.configurations.update(settings_dict)
        item = Gio.MenuItem.new(name, "win.settings")
        item.set_attribute_value("target", GLib.Variant.new_string(key))
        self.settings_section.append_item(item)

        self.save_dialog.close()

    def on_save_settings_name_entry_changed(self, entry):
        if entry.get_text_length() != 0:
            self.save_settings_button.set_sensitive(True)
        else:
            self.save_settings_button.set_sensitive(False)

    def on_save_settings_extensions_entry_changed(self, entry):
        extensions_text = entry.get_text()

        if extensions_text == "":
            entry.remove_css_class("error")
            return

        entered_exts = [ext.strip() for ext in extensions_text.split(',')]

        if all(ext in allowed_extensions for ext in entered_exts):
            entry.remove_css_class("error")
        else:
            entry.add_css_class("error")

    def on_save_settings(self, *args):
        self.save_settings_name_entry.set_text("")
        self.save_settings_extensions_entry.set_text("")
        self.save_settings_expander.set_expanded(False)
        self.save_dialog.present(self)

    def set_settings_from_name(self, name):
        self.logger.debug("settings from name")
        if name == "custom":
            return

        # Get the default settings and change the ones defined by the chosen presets
        options = self.window_settings.get_default_user_customizable_settings()
        for key, value in self.configurations[name]["view-settings"].items():
            options[key] = value

        # Set all the settings
        for key, value in options.items():
            self.window_settings.set_setting(key, value)

        # Update all the viewer settings, to support settings without UI
        self.f3d_viewer.update_options(options)

        # Set all the settings not related to the viewer
        for key, value in self.configurations[name]["other-settings"].items():
            self.window_settings.set_setting(key, value)

    def check_for_options_change(self):
        if self.block_reload:
            return

        state_name = self.settings_action.get_state().get_string()
        if state_name == "custom":
            return

        self.logger.debug(f"Checking for changed options from {state_name}")

        state_options = self.window_settings.get_default_user_customizable_settings()

        for key, value in self.configurations[state_name]["view-settings"].items():
            state_options[key] = value

        for key, value in self.configurations[state_name]["other-settings"].items():
            state_options[key] = value

        current_settings = self.window_settings.get_user_customized_settings()
        for key, value in state_options.items():
            if key in current_settings:
                if current_settings[key] != value:
                    self.logger.info(
                        f"current key: {key}'s value is {current_settings[key]} != {value}")
                    self.change_setting_state(GLib.Variant("s", "custom"))
                    return

    def periodic_check_for_file_change(self):
        if self.filepath == "":
            return True

        changed = self.update_time_stamp()
        if changed:
            self.logger.debug("file changed")
            self.load_file(preserve_orientation=True, override=True)

        if self.window_settings.get_setting("auto-reload").value:
            return True
        return False

    def update_time_stamp(self):
        try:
            stamp = os.stat(self.filepath).st_mtime
            if stamp != self._cached_time_stamp:
                self._cached_time_stamp = stamp
                return True
            return False
        except Exception:
            return False

    def change_setting_state(self, state):
        self.logger.debug(f"Requested changing settings to {state}")

        if state.get_string() == "custom":
            self.save_settings_action.set_enabled(True)
            self.settings_action.set_state(state)
            return

        self.set_settings_from_name(state.get_string())

        self.settings_action.set_state(state)

        self.save_settings_action.set_enabled(False)

        self.update_background_color()

    def get_gimble_limit(self):
        return self.distance / 10

    def open_file_chooser(self, *args):
        file_filter = Gtk.FileFilter(name=_("All supported formats"))

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
        try:
            file = dialog.open_finish(response)
        except Exception as e:
            self.logger.error(f"Exception Opening file: {e}")
            return

        if file:
            filepath = file.get_path()
            self.logger.info("open file response")
            self.load_file(filepath=filepath)

    def load_file(self, **kwargs):
        self.startup_stack.set_visible_child_name("loading_page")
        self.stack.set_visible_child_name("startup_page")
        self.loading_label.set_label(
            _("Loading {}").format(
                os.path.basename(kwargs.get("filepath", "Nothing"))))
        self.block_reload = True
        GLib.timeout_add(
            100,
            lambda *args: threading.Thread(
                target=self._load_file, kwargs=(kwargs)).start())

    def _load_file(self, **kwargs):
        filepath = kwargs.get("filepath", None)
        override = kwargs.get("override", False)
        preserve_orientation = kwargs.get("preserve_orientation", False)
        add_file = kwargs.get("add_file", False)

        if preserve_orientation:
            camera_state = self.f3d_viewer.get_camera_state()

        if filepath is None:
            filepath = self.filepath

        if filepath == "" or filepath is None:
            return

        self.logger.debug(
            f"load file: {filepath}")

        self.change_checker.stop()

        if (self.window_settings.get_setting("auto-best").value
                and not override) and not add_file:
            self.logger.debug("choosing best settings")
            settings = "general"
            for key, value in self.configurations.items():
                pattern = value["formats"]
                if pattern == ".*()":
                    continue
                if re.search(pattern, filepath):
                    settings = key
            self.logger.debug(f"best settings is {settings}")
            self.change_setting_state(GLib.Variant("s", settings))

        if self.f3d_viewer.supports(filepath):
            if add_file:
                if not self.f3d_viewer.add_file(filepath):
                    self.on_file_not_opened(filepath)
                    return
            else:
                if not self.f3d_viewer.load_file(filepath):
                    self.on_file_not_opened(filepath)
                    return
        else:
            self.on_file_not_opened(filepath)
            return

        if preserve_orientation:
            self.f3d_viewer.set_camera_state(camera_state)

        self.filepath = filepath
        self.on_file_opened()

    def on_file_opened(self):
        self.logger.debug("on file opened")

        self.update_time_stamp()
        if self.window_settings.get_setting("auto-reload").value:
            self.change_checker.run()

        self.file_name = os.path.basename(self.filepath)

        self.set_title(_("Exhibit - {}").format(self.file_name))
        self.title_widget.set_subtitle(self.file_name)
        self.stack.set_visible_child_name("3d_page")

        self.no_file_loaded = False

        self.update_background_color()

        if self.f3d_viewer.upper_time_range == 0.0:
            self.animation_group.set_visible(False)
        else:
            self.animation_group.set_visible(True)

        self.block_reload = False
        GLib.timeout_add(100, self.f3d_viewer.done)

    def on_file_not_opened(self, filepath):
        self.logger.debug("on file not opened")

        self.set_title(_("Exhibit"))
        if self.no_file_loaded:
            self.stack.set_visible_child_name("startup_page")
            self.startup_stack.set_visible_child_name("error_page")
        else:
            self.send_toast(_("Can't open") + " " + os.path.basename(filepath))

        self.update_background_color()

        self.block_reload = False

    def send_toast(self, message):
        toast = Adw.Toast(title=message, timeout=2)
        self.toast_overlay.add_toast(toast)

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
        except Exception:
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

    def orthonographic_state_changed(self, state):
        self.window_settings.set_setting("orthographic", state.get_boolean())

        self.f3d_viewer.update_options({"orthographic": state.get_boolean()})

    @Gtk.Template.Callback("on_drop_received")
    def on_drop_received(self, drop, value, x, y):
        filepath = value.get_files()[0].get_path()
        extension = "*." + os.path.splitext(filepath)[1][1:].lower()

        if extension in image_patterns:
            self.load_hdri(filepath)
        elif extension in file_patterns:
            self.logger.info("drop received")
            self.load_file(filepath=filepath)

    @Gtk.Template.Callback("on_drop_enter")
    def on_drop_enter(self, drop_target, *args):
        drop_target.get_widget().set_visible_child_name("drop")

    @Gtk.Template.Callback("on_drop_leave")
    def on_drop_leave(self, drop_target, *args):
        drop_target.get_widget().set_visible_child_name("content")

    @Gtk.Template.Callback("on_close_sidebar_clicked")
    def on_close_sidebar_clicked(self, *args):
        self.split_view.set_show_sidebar(False)

    def on_open_with_external_app(self, *args):
        try:
            file = Gio.File.new_for_path(self.filepath)
        except Exception:
            self.logger.error("Failed to construct a new Gio.File from path.")
        else:
            launcher = Gtk.FileLauncher.new(file)
            launcher.set_always_ask(True)

            def open_file_finish(_, result, *args):
                try:
                    launcher.launch_finish(result)
                except Exception as e:
                    self.logger.error(e)

            launcher.launch(self, None, open_file_finish)

    @Gtk.Template.Callback("on_apply_breakpoint")
    def on_apply_breakpoint(self, *args):
        self.applying_breakpoint = True
        self.split_view.set_collapsed(True)
        self.split_view.set_show_sidebar(False)
        self.applying_breakpoint = False

    @Gtk.Template.Callback("on_unapply_breakpoint")
    def on_unapply_breakpoint(self, *args):
        state = self.window_settings.get_setting("sidebar-show").value
        self.applying_breakpoint = True
        self.split_view.set_collapsed(False)
        self.split_view.set_show_sidebar(state)
        self.applying_breakpoint = False

    @Gtk.Template.Callback("on_split_view_show_sidebar_changed")
    def on_split_view_show_sidebar_changed(self, *args):
        if self.applying_breakpoint:
            return
        state = self.split_view.get_show_sidebar()
        self.window_settings.set_setting("sidebar-show", state)

    def on_play_button_clicked(self, btn):
        self.f3d_viewer.playing = not self.f3d_viewer.playing

    def on_playing_changed(self, *args):
        if self.f3d_viewer.playing:
            self.play_button.set_icon_name("media-playback-pause-symbolic")
            self.play_button.set_tooltip_text(_("Stop"))
        else:
            self.play_button.set_icon_name("media-playback-start-symbolic")
            self.play_button.set_tooltip_text(_("Start"))

    #
    # Function called when the HDRI is deleted/added...

    def on_delete_skybox(self, *args):
        self.window_settings.set_setting("hdri-file", "")
        self.window_settings.set_setting("hdri-skybox", False)
        self.use_skybox_switch.set_active(False)
        options = {
            "hdri-file": "",
            "hdri-skybox": False}
        self.f3d_viewer.update_options(options)
        self.check_for_options_change()

    def load_hdri(self, filepath):
        self.window_settings.set_setting("hdri-file", filepath)
        self.window_settings.set_setting("hdri-skybox", True)
        self.use_skybox_switch.set_active(True)
        self.hdri_file_row.set_filename(filepath)
        options = {
            "hdri-file": filepath,
            "hdri-skybox": True}
        self.f3d_viewer.update_options(options)
        self.check_for_options_change()

    def create_action(self, name, callback):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        return action

    def generate_thumbnail(self, hdri_file_path, width=300, height=200):
        base_name = os.path.basename(hdri_file_path)
        name, _ = os.path.splitext(base_name)

        thumbnail_name = f"{name}.jpeg"
        thumbnail_filepath = os.path.join(
            self.hdri_thumbnails_path, thumbnail_name)

        with Image(filename=hdri_file_path) as img:
            img.thumbnail(width, height)
            img.gamma(1.7)
            img.brightness_contrast(0, -5)
            img.format = 'jpeg'
            img.save(filename=thumbnail_filepath)

        return thumbnail_filepath

    @Gtk.Template.Callback("on_close_request")
    def on_close_request(self, window):
        self.logger.debug("window closed, saving settings")
        self.saved_settings.set_int(
            "startup-width", window.get_width())
        self.saved_settings.set_int(
            "startup-height", window.get_height())
        self.saved_settings.set_boolean(
            "startup-sidebar-show", window.split_view.get_show_sidebar())
        self.saved_settings.set_boolean(
            "auto-best", self.window_settings.get_setting("auto-best").value)


def rgb_to_list(rgb):
    values = tuple(int(x) / 255 for x in rgb[4:-1].split(','))
    return values


def list_to_rgb(lst):
    return f"rgb({int(lst[0] * 255)},{int(lst[1] * 255)},{int(lst[2] * 255)})"


def list_files(directory):
    items = os.listdir(directory)
    files = [
        item for item in items if os.path.isfile(os.path.join(directory, item))
    ]
    return files
