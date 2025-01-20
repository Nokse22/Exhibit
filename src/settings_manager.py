# settings_manager.py
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later


from gi.repository import Gio, GObject

from enum import IntEnum

from . import logger_lib

#   Other special
#   functions if  <──────┐                 On change
#   connected            │     ┌─────────┐ update the UI
#                        │     │         ∨
#                       ┌─────────┐     ┌──┐
#      Update       ━━━▶│ListStore│     │UI│
#      the settings     └─────────┘     └──┘
#                        │     ∧         │
#                        │     └─────────┘ On change update
#                        │                 the ListStore
#        ┏━━━━━━┓        │ On change
#        ┃Viewer┃<───────┘ update the
#        ┗━━━━━━┛          view options
#
# Made with  ASCII Draw


class SettingType(IntEnum):
    VIEW = 0
    OTHER = 1
    INTERNAL = 2


class Setting(GObject.Object):
    __gtype_name__ = 'Setting'

    __gsignals__ = {
        'changed': (
            GObject.SignalFlags.RUN_FIRST, None, (str, int, )),
        'changed-no-ui-update': (
            GObject.SignalFlags.RUN_FIRST, None, (str, int, )),
    }

    def __init__(self, name, value, setting_type):
        super().__init__()

        self._name = name
        self._value = value
        self._type = setting_type

    @GObject.Property(type=str)
    def name(self) -> str:
        return self._name

    @GObject.Property(type=str)
    def value(self) -> str:
        return self._value

    @GObject.Property(type=str)
    def type(self) -> str:
        return self._type

    def set_value(self, value):
        if value != self._value:
            self._value = value
            self.emit("changed", self._name, self._type)

    def set_value_without_ui_update(self, value):
        if value != self._value:
            self._value = value
            self.emit("changed-no-ui-update", self._name, self._type)

    def __repr__(self):
        return f"<Setting {self._name}: {self._value}>"


class WindowSettings(Gio.ListStore):
    __gtype_name__ = 'WindowSettings'

    __gsignals__ = {
        'changed-view': (GObject.SignalFlags.RUN_FIRST, None, (Setting, )),
        'changed-other': (GObject.SignalFlags.RUN_FIRST, None, (Setting, )),
        'changed-internal': (GObject.SignalFlags.RUN_FIRST, None, (Setting, )),
    }

    default_settings = {
        "translucency-support": True,
        "tone-mapping": True,
        "ambient-occlusion": False,
        "anti-aliasing": True,
        "hdri-ambient": False,
        "light-intensity": 1.5,

        "show-edges": False,
        "edges-width": 1.0,

        "sprite-enabled": False,
        "point-size": 1.0,
        "sprites-type": "sphere",

        "sprites-size": 1.0,

        "model-metallic": 0.0,
        "model-roughness": 0.3,
        "model-opacity": 1.0,

        "armature-enable": False,

        "scivis-component": -1,
        "cells": True,
        "scivis-enabled": False,
        "model-color": (1.0, 1.0, 1.0),

        "grid": True,
        "grid-absolute": False,

        "hdri-skybox": False,
        "hdri-file": "",
        "blur-background": True,
        "blur-coc": 20.0,

        "bg-color": (1.0, 1.0, 1.0),

        "up": "+Y",
        "orthographic": False,

        "animation-index": 0,
        "animation-time": 0.0,

        # There is no UI for the following ones

        # "texture-matcap": "",
        # "texture-base-color": "",
        # "emissive-factor": (1.0, 1.0, 1.0),
        # "texture-emissive": "",
        # "texture-material": "",
        "normal-scale": 1.0,
        # "texture-normal": "",
        "volume": False,
        "inverse": False,
        # "final-shader": "",
        # "grid-unit": 10.0,
        # "grid-subdivisions": 10,
        "grid-color": (0.0, 0.0, 0.0),
        # "scalar": ""
    }

    other_settings = {
        "use-color": False,
        "point-up": True,
        "auto-reload": True
    }

    internal_settings = {
        "auto-best": True,
        "sidebar-show": True
    }

    def __init__(self):
        super().__init__()

        self.logger = logger_lib.logger

        for name, value in self.default_settings.items():
            setting = Setting(name, value, SettingType.VIEW)
            setting.connect("changed", self.on_view_setting_changed)
            setting.connect(
                "changed-no-ui-update", self.on_other_setting_changed)
            self.append(setting)

        for name, value in self.other_settings.items():
            setting = Setting(name, value, SettingType.OTHER)
            setting.connect("changed", self.on_other_setting_changed)
            setting.connect(
                "changed-no-ui-update", self.on_other_setting_changed)
            self.append(setting)

        for name, value in self.internal_settings.items():
            setting = Setting(name, value, SettingType.INTERNAL)
            setting.connect("changed", self.on_internal_setting_changed)
            setting.connect(
                "changed-no-ui-update", self.on_other_setting_changed)
            self.append(setting)

    def sync_all_settings(self):
        for setting in self:
            setting.emit("changed", setting.name, setting.type)

    def on_view_setting_changed(self, setting, name, enum):
        self.emit("changed-view", setting)

    def on_other_setting_changed(self, setting, name, enum):
        self.emit("changed-other", setting)

    def on_internal_setting_changed(self, setting, name, enum):
        self.emit("changed-internal", setting)

    def set_setting(self, key, val, update=True):
        for index, setting in enumerate(self):
            if key == setting.name:
                if update:
                    setting.set_value(val)
                else:
                    setting.set_value_without_ui_update(val)
                return
        self.logger.warning(f"{key} key not present")

    def get_setting(self, key):
        for setting in self:
            if key == setting.name:
                return setting

    def get_default_user_customizable_settings(self):
        settings = self.default_settings.copy()
        settings.update(self.other_settings)
        return settings

    def get_user_customized_settings(self):
        settings = self.get_view_settings()
        settings.update(self.get_other_settings())
        return settings

    def set_settings(self, dictionary):
        for key, value in dictionary:
            self.set_setting(key, value)

    def get_view_settings(self):
        options = {}
        for setting in self:
            if setting.type == SettingType.VIEW:
                options[setting.name] = setting.value
        return options

    def get_other_settings(self):
        options = {}
        for setting in self:
            if setting.type == SettingType.OTHER:
                options[setting.name] = setting.value
        return options

    def __repr__(self):
        out = ""
        for setting in self:
            out += f"{setting.name}:    {setting.value}\n"
        return out
