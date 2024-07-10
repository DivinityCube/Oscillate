import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Adw, Gst, GLib, Gio

class CitrusMediaPlayer(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

        # Initialize GStreamer
        Gst.init(None)

    def on_activate(self, app):
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_default_size(350, 100)
        self.win.set_title("Citrus Media Player")

        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.win.set_content(main_box)

        # Create a header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        # Create a menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        header.pack_end(menu_button)

        # Create a menu model
        menu = Gio.Menu()
        menu.append("About", "app.about")
        menu_button.set_menu_model(menu)

        # Create an about action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_activate)
        self.add_action(about_action)

        # Create a content area
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        main_box.append(content)

        # Create a horizontal box for controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, halign=Gtk.Align.CENTER)
        content.append(controls_box)

        # Create buttons
        self.play_button = Gtk.Button.new_from_icon_name("media-playback-start-symbolic")
        self.stop_button = Gtk.Button.new_from_icon_name("media-playback-stop-symbolic")

        # Add buttons to the horizontal box
        controls_box.append(self.play_button)
        controls_box.append(self.stop_button)

        # Connect button signals
        self.play_button.connect("clicked", self.on_play_clicked)
        self.stop_button.connect("clicked", self.on_stop_clicked)

        # Create an open button in the header bar
        open_button = Gtk.Button.new_from_icon_name("document-open-symbolic")
        open_button.connect("clicked", self.on_open_clicked)
        header.pack_start(open_button)

        # Create a label to show the current file
        self.title_label = Gtk.Label(label="No file selected", ellipsize=3)
        content.append(self.title_label)

        # Create GStreamer pipeline
        self.pipeline = Gst.ElementFactory.make("playbin", "player")
        if not self.pipeline:
            print("Error: Could not create GStreamer pipeline.")
            sys.exit(1)

        # Create a bus to get events from GStreamer pipeline
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

        self.win.present()

    def on_about_activate(self, action, param):
        about = Adw.AboutWindow(transient_for=self.win,
                                application_name="Citrus Media Player",
                                application_icon="audio-x-generic",
                                developer_name="Taysy",
                                version="0.1.0",
                                developers=["Taysy"],
                                copyright="© 2024 Taysy")
        about.present()

    def on_open_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a media file",
            transient_for=self.win,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Open", Gtk.ResponseType.ACCEPT
        )

        filter_media = Gtk.FileFilter()
        filter_media.set_name("Media files")
        filter_media.add_mime_type("audio/mpeg")
        filter_media.add_mime_type("video/mp4")
        dialog.add_filter(filter_media)

        dialog.connect("response", self.on_file_dialog_response)
        dialog.present()

    def on_file_dialog_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file:
                self.pipeline.set_state(Gst.State.NULL)
                self.pipeline.set_property("uri", file.get_uri())
                self.title_label.set_text("Loading...")
                self.play_button.set_sensitive(True)
        dialog.destroy()

    def on_play_clicked(self, button):
        state = self.pipeline.get_state(Gst.CLOCK_TIME_NONE)[1]
        if state == Gst.State.PLAYING:
            self.pipeline.set_state(Gst.State.PAUSED)
            self.play_button.set_icon_name("media-playback-start-symbolic")
        else:
            self.pipeline.set_state(Gst.State.PLAYING)
            self.play_button.set_icon_name("media-playback-pause-symbolic")

    def on_stop_clicked(self, button):
        self.pipeline.set_state(Gst.State.NULL)
        self.title_label.set_text("No file selected")
        self.play_button.set_icon_name("media-playback-start-symbolic")
        self.play_button.set_sensitive(False)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.pipeline.set_state(Gst.State.NULL)
            self.title_label.set_text("No file selected")
            self.play_button.set_icon_name("media-playback-start-symbolic")
            self.play_button.set_sensitive(False)
        elif t == Gst.MessageType.ERROR:
            self.pipeline.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print(f"Error: {err}", debug)
            self.title_label.set_text(f"Error: {err}")
            self.play_button.set_sensitive(False)
        elif t == Gst.MessageType.TAG:
            tags = message.parse_tag()
            if tags.get_string('title')[0]:
                title = tags.get_string('title')[1]
                self.title_label.set_text(title)

def main(version):
    app = CitrusMediaPlayer(application_id="com.example.CitrusMediaPlayer")
    return app.run(None)

if __name__ == "__main__":
    sys.exit(main("0.1.0"))