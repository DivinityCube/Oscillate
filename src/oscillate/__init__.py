import os
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, GLib

# Load resources at startup
try:
    resource_path = os.path.join(os.path.dirname(__file__), 'com.example.Oscillate.gresource')
    resource = Gio.Resource.load(resource_path)
    resource._register()
except Exception as e:
    print(f"Error loading resources: {e}")
    # List directory contents for debugging
    print("Directory contents:", os.listdir(os.path.dirname(__file__)))
