import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import OscillateWindow
from .preferences import OscillatePreferences

class OscillateApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='com.example.Oscillate',
                        flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)
        self.create_action('delete-song', self.on_delete_song_action)

    def on_delete_song_action(self, action, param):
        """Handle delete-song action at application level."""
        win = self.props.active_window
        if win:
            win.delete_selected_song()

    def do_activate(self):
        """Called when the application is activated."""
        win = self.props.active_window
        if not win:
            win = OscillateWindow(application=self)
        win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name='Oscillate',
            application_icon='com.example.Oscillate',
            developer_name='Tay Rake',
            version='1.5-INDEV',
            developers=['Tay Rake'],
            copyright='© 2024 - 2025 Tay Rake'
        )
        about.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        if not self.props.active_window:
            return

        prefs = OscillatePreferences(parent=self.props.active_window)
        prefs.present()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action."""
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

def main():
    """The application's entry point."""
    app = OscillateApplication()
    return app.run(sys.argv)
