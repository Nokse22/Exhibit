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

import os

class ImageThumbnail(Gtk.FlowBoxChild):
    __gtype_name__ = 'ImageThumbnail'

    def __init__(self, file_thumbnail, hdri_file):
        super().__init__()

        self.hdri_file = hdri_file

        file = Gio.File.new_for_path(file_thumbnail)
        image = Gtk.Picture(
            file=file,
            css_classes=["suggested-picture"],
            hexpand=True,
            vexpand=True,
            content_fit=Gtk.ContentFit.COVER
        )
        self.set_child(image)

        base_name = os.path.basename(hdri_file)
        self.set_tooltip_text(base_name)


@Gtk.Template(resource_path='/io/github/nokse22/Exhibit/ui/file_row.ui')
class FileRow(Adw.PreferencesRow):
    __gtype_name__ = 'FileRow'

    __gsignals__ = {
        'open-file': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'delete-file': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'file-added': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    file_button = Gtk.Template.Child()
    filename_label = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()
    drop_target = Gtk.Template.Child()
    suggestions_box = Gtk.Template.Child()

    filepath = ""

    def __init__(self):
        super().__init__()

        self.title = ""

        self.suggested_files_n = 0

        self.file_button.connect("clicked", self.on_open_clicked)
        self.delete_button.connect("clicked", self.on_delete_clicked)
        self.suggestions_box.connect("child-activated", self.on_image_activated)
        self.drop_target.connect("drop", self.on_drop_received)

        self.drop_target.set_gtypes([Gdk.FileList])

    def on_open_clicked(self, btn):
        self.emit("open-file")

    def set_filename(self, filepath):
        if filepath == "":
            return

        self.filepath = filepath
        self.filename_label.set_label(os.path.basename(filepath))
        self.filename_label.set_visible(True)
        self.delete_button.set_visible(True)

    def on_delete_clicked(self, btn):
        self.filename_label.set_visible(False)
        self.delete_button.set_visible(False)
        self.emit("delete-file")

    def on_drop_received(self, drop, value, x, y):
        filepath = value.get_files()[0].get_path()
        self.emit("file-added", filepath)
        self.set_filename(filepath)

    def add_suggested_file(self, file_thumbnail, filepath):
        if os.path.isfile(filepath):
            self.suggestions_box.set_visible(True)

            hdri_thumbnail = ImageThumbnail(file_thumbnail, filepath)
            self.suggestions_box.append(hdri_thumbnail)

            self.suggested_files_n += 1
            height = ((self.suggested_files_n + 3) // 4) * 70
            self.suggestions_box.set_size_request(-1, height)

    def on_image_activated(self, flow_box, child):
        filepath = child.hdri_file
        self.set_filename(filepath)
        self.emit("file-added", filepath)
