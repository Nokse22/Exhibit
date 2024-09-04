import gi
from gi.repository import GLib

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

GLib.setenv("GSK_RENDERER", "gl", False)
GLib.setenv("GDK_DEBUG", "gl-prefer-gl", True)
