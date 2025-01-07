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

from gi.repository import Gtk, GLib, GObject

import f3d

from ..vector_math import p_dist, v_abs, v_norm, v_add, v_sub, v_mul, v_dot_p
from .. import logger_lib

up_dirs_vector = {
    "-X": (-1.0, 0.0, 0.0),
    "+X": (1.0, 0.0, 0.0),
    "-Y": (0.0, -1.0, 0.0),
    "+Y": (0.0, 1.0, 0.0),
    "-Z": (0.0, 0.0, -1.0),
    "+Z": (0.0, 0.0, 1.0),
}


@Gtk.Template(resource_path="/io/github/nokse22/Exhibit/ui/f3d_viewer.ui")
class F3DViewer(Gtk.GLArea):
    __gtype_name__ = "F3DViewer"

    keys = {
        "grid": "render.grid.enable",
        "grid-absolute": "render.grid.absolute",
        "translucency-support": "render.effect.translucency_support",
        "tone-mapping": "render.effect.tone_mapping",
        "ambient-occlusion": "render.effect.ambient_occlusion",
        "anti-aliasing": "render.effect.anti_aliasing",
        "hdri-ambient": "render.hdri.ambient",
        "hdri-skybox": "render.background.skybox",
        "light-intensity": "render.light.intensity",
        "orthographic": "scene.camera.orthographic",
        "blur-background": "render.background.blur.enable",
        "blur-coc": "render.background.blur.coc",
        "bg-color": "render.background.color",
        "show-edges": "render.show_edges",
        "edges-width": "render.line_width",
        "up": "scene.up_direction",
        "point-sprites": "model.point_sprites.enable",
        "point-size": "render.point_size",
        "model-color": "model.color.rgb",
        "model-metallic": "model.material.metallic",
        "model-roughness": "model.material.roughness",
        "model-opacity": "model.color.opacity",
        "comp": "model.scivis.component",
        "hdri-file": "render.hdri.file",
        "cells": "model.scivis.cells",

        # The following settings don't have an UI

        "texture-matcap": "model.matcap.texture",
        "texture-base-color": "model.color.texture",
        "emissive-factor": "model.emissive.factor",
        "texture-emissive": "model.emissive.texture",
        "texture-material": "model.material.texture",
        "normal-scale": "model.normal.scale",
        "texture-normal": "model.normal.texture",
        "point-type": "model.point_sprites.type",
        "volume": "model.volume.enable",
        "inverse": "model.volume.inverse",
        "final-shader": "render.effect.final_shader",
        "grid-unit": "render.grid.unit",
        "grid-subdivisions": "render.grid.subdivisions",
        "grid-color": "render.grid.color",
        "scalar": "model.scivis.array_name",
        "animation-index": "scene.animation.index"
    }

    def __init__(self, *args):

        self.logger = logger_lib.logger

        f3d.Log.set_use_coloring(True)
        f3d.Log.set_verbose_level(f3d.Log.DEBUG)
        f3d.Log.print(f3d.Log.DEBUG, 'debug')

        self.set_auto_render(True)
        self.connect("realize", self.on_realize)
        self.connect("render", self.on_render)
        self.connect("resize", self.on_resize)

        self.settings = {
            "scene.up_direction": "+Y",
            "model.scivis.cells": True,
            "model.scivis.array_name": "",
            "render.hdri.ambient": False,
        }

        self.prev_pan_offset = 0
        self.drag_prev_offset = (0, 0)
        self.drag_start_angle = 0

        self.always_point_up = True

        self.prev_scale = 1

        self.distance = 0

        self.is_showed = False

        self._animation_time = 0
        self._playing = False

        self.engine = f3d.Engine.create_external_egl()
        self.scene = self.engine.scene
        self.window = self.engine.window
        self.camera = self.window.camera

        self.engine.autoload_plugins()

        self.engine.options.update(self.settings)

    @GObject.Property(type=float)
    def upper_time_range(self):
        _lower, upper = self.scene.animation_time_range()
        print("TIME RANGE", _lower, upper)
        return upper

    @GObject.Property(type=float)
    def lower_time_range(self):
        lower, _upper = self.scene.animation_time_range()
        print("TIME RANGE", lower, _upper)
        return lower

    @GObject.Property(type=float)
    def animation_time(self):
        return self._animation_time

    @animation_time.setter
    def animation_time(self, value):
        self._animation_time = value
        self.scene.load_animation_time(self._animation_time)
        self.queue_render()

    @GObject.Property(type=bool, default=False)
    def playing(self):
        return self._playing

    @playing.setter
    def playing(self, value):
        self._playing = value

        if self._playing:
            if self.animation_time >= self.upper_time_range:
                self.animation_time = self.lower_time_range
            GLib.timeout_add(10, self._advance_animation)

    def _advance_animation(self):
        self.animation_time = self.animation_time + 0.01
        if self.animation_time >= self.upper_time_range:
            self.playing = False
        return self._playing

    def reset_to_bounds(self):
        self.camera.reset_to_bounds()
        self.get_distance()
        self.queue_render()

    def front_view(self, *args):
        up_v = up_dirs_vector[self.settings["scene.up_direction"]]
        vector = v_mul(tuple([up_v[2], up_v[0], up_v[1]]), 1000)
        self.camera.position = v_add(self.camera.focal_point, vector)
        self.camera.view_up = up_dirs_vector[self.settings["scene.up_direction"]]
        self.camera.reset_to_bounds()
        self.get_distance()
        self.queue_render()

    def right_view(self, *args):
        up_v = up_dirs_vector[self.settings["scene.up_direction"]]
        vector = v_mul(tuple([up_v[1], up_v[2], up_v[0]]), 1000)
        self.camera.position = v_add(self.camera.focal_point, vector)
        self.camera.view_up = up_dirs_vector[self.settings["scene.up_direction"]]
        self.camera.reset_to_bounds()
        self.get_distance()
        self.queue_render()

    def top_view(self, *args):
        up_v = up_dirs_vector[self.settings["scene.up_direction"]]
        vector = v_mul(up_v, 1000)
        self.camera.position = v_add(self.camera.focal_point, vector)
        vector = v_mul(tuple([up_v[1], up_v[2], up_v[0]]), 1000)
        self.camera.view_up = vector
        self.camera.reset_to_bounds()
        self.get_distance()
        self.queue_render()

    def isometric_view(self, *args):
        up_v = up_dirs_vector[self.settings["scene.up_direction"]]
        vector = v_add(
            tuple([up_v[2], up_v[0], up_v[1]]),
            tuple([up_v[1], up_v[2], up_v[0]])
        )
        self.camera.position = v_mul(v_norm(v_add(vector, up_v)), 1000)
        self.camera.view_up = up_dirs_vector[self.settings["scene.up_direction"]]
        self.camera.reset_to_bounds()
        self.get_distance()
        self.queue_render()

    def update_options(self, options):
        f3d_options = {}
        for key, value in options.items():
            if key in self.keys:
                f3d_key = self.keys[key]
                self.settings[f3d_key] = value
                f3d_options[f3d_key] = value

        print(f3d_options)
        self.engine.options.update(f3d_options)
        self.queue_render()

    def render_image(self):
        self.get_context().make_current()
        img = self.window.render_to_image()
        # print(img.to_terminal_text())
        return img

    def supports(self, filepath):
        return self.scene.supports(filepath)

    def load_file(self, filepath):
        if self.settings["render.hdri.ambient"]:
            f3d_options = {"render.hdri.ambient": False}
            self.engine.options.update(f3d_options)

        self.scene.clear()

        self.scene.add(filepath)
        self.notify("lower-time-range")
        self.notify("upper-time-range")

    def add_file(self, filepath):
        if self.settings["render.hdri.ambient"]:
            f3d_options = {"render.hdri.ambient": False}
            self.engine.options.update(f3d_options)

        self.scene.add(filepath)

        self.notify("lower-time-range")
        self.notify("upper-time-range")

        self.get_distance()

    def done(self):
        if self.settings["render.hdri.ambient"]:
            f3d_options = {"render.hdri.ambient": True}
            self.engine.options.update(f3d_options)
            self.queue_render()

        # self.reset_to_bounds()

    def on_resize(self, gl_area, width, height):
        self.width = width
        self.height = height

    def on_realize(self, area):
        if self.get_context() is None:
            self.logger.critical("Could not create GL context")

    def on_show(self, *args):
        self.is_showed = True
        self.logger.debug("F3D Viewer has been showed")

        def _set_hdri_ambient_true():
            f3d_options = {"render.hdri.ambient": True}
            self.engine.options.update(f3d_options)
            self.queue_render()

        if self.settings["render.hdri.ambient"]:
            GLib.timeout_add(100, _set_hdri_ambient_true)

    def on_render(self, area, ctx):
        self.get_context().make_current()
        self.window.size = self.width, self.height
        self.window.render()

    def get_camera_to_focal_distance(self):
        up = up_dirs_vector[self.settings["scene.up_direction"]]
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

    def get_gimble_limit(self):
        return self.distance / 10

    def get_distance(self):
        self.distance = p_dist(self.camera.position, (0, 0, 0))

    def pan(self, x, y, z):
        val = self.distance / 40
        self.camera.pan(x * val, y * val, z * val)
        self.queue_render()

    def rotate_camera(self, direction):
        val = self.distance / 40

        focal_point = self.camera.focal_point

        match direction:
            case "left":
                self.camera.pan(-val, 0, 0)
                self.camera.focal_point = focal_point
            case "right":
                self.camera.pan(val, 0, 0)
                self.camera.focal_point = focal_point
            case "up":
                dist, direction = self.get_camera_to_focal_distance()
                if dist > self.get_gimble_limit() or (
                    dist < self.get_gimble_limit() and direction == -1
                ):
                    self.camera.pan(0, val, 0)
                    self.camera.focal_point = focal_point
            case "down":
                dist, direction = self.get_camera_to_focal_distance()
                if dist > self.get_gimble_limit() or (
                    dist < self.get_gimble_limit() and direction == 1
                ):
                    self.camera.pan(0, -val, 0)
                    self.camera.focal_point = focal_point

        if self.always_point_up:
            up = up_dirs_vector[self.settings["scene.up_direction"]]
            self.camera.view_up = up

        self.queue_render()

    def set_view_up(self, direction):
        self.camera.view_up = direction
        self.queue_render()

    def set_camera_state(self, state):
        self.camera.state = state
        self.queue_render()

    def get_camera_state(self):
        return self.camera.state

    @Gtk.Template.Callback("on_scroll")
    def on_scroll(self, gesture, dx, dy):
        if self.settings["scene.camera.orthographic"]:
            self.camera.zoom(1 - 0.1 * dy)
        else:
            self.camera.dolly(1 - 0.1 * dy)
        self.get_distance()
        self.queue_render()

    @Gtk.Template.Callback("on_zoom_scale_changed")
    def on_zoom_scale_changed(self, zoom_gesture, scale):
        self.camera.dolly(1 - self.prev_scale + scale)
        self.prev_scale = scale
        self.get_distance()
        self.queue_render()

    @Gtk.Template.Callback("on_drag_update")
    def on_drag_update(self, gesture, x_offset, y_offset):
        if gesture.get_current_button() == 1:
            dist, direction = self.get_camera_to_focal_distance()
            y = -(self.drag_prev_offset[1] - y_offset) * 0.5
            x = (self.drag_prev_offset[0] - x_offset) * 0.5
            if not self.always_point_up:
                self.camera.elevation(y)
                self.camera.azimuth(x)
            else:
                if (
                    dist > self.get_gimble_limit()
                    or (dist < self.get_gimble_limit())
                    and (direction == 1 and y < 0)
                    or (dist < self.get_gimble_limit() and direction == -1 and y > 0)
                ):
                    self.camera.elevation(y)
                self.camera.azimuth(x)
        elif gesture.get_current_button() == 2:
            self.camera.pan(
                (self.drag_prev_offset[0] - x_offset)
                * (0.0000001 * self.width + 0.001 * self.distance),
                -(self.drag_prev_offset[1] - y_offset)
                * (0.0000001 * self.height + 0.001 * self.distance),
                0,
            )

        if self.always_point_up:
            up = up_dirs_vector[self.settings["scene.up_direction"]]
            self.camera.view_up = up

        self.queue_render()

        self.drag_prev_offset = (x_offset, y_offset)

    @Gtk.Template.Callback("on_drag_end")
    def on_drag_end(self, gesture, *args):
        self.drag_prev_offset = (0, 0)
