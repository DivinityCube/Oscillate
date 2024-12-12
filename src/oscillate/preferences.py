# src/oscillate/preferences.py
from gi.repository import Adw, Gtk, Gio

class OscillatePreferences(Adw.PreferencesWindow):
    """Preferences window for Oscillate."""

    def __init__(self, parent, **kwargs):
        super().__init__(**kwargs)

        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title("Preferences")

        # Create settings
        self.settings = Gio.Settings.new("com.example.Oscillate")

        # Playback page
        playback_page = Adw.PreferencesPage()
        playback_page.set_title("Playback")
        playback_page.set_icon_name("media-playback-start-symbolic")
        self.add(playback_page)

        # Playback behavior group
        behavior_group = Adw.PreferencesGroup()
        behavior_group.set_title("Behavior")
        playback_page.add(behavior_group)

        # Auto-play switch
        autoplay_row = Adw.ActionRow()
        autoplay_row.set_title("Auto-play")
        autoplay_row.set_subtitle("Start playing automatically when adding songs")
        autoplay_switch = Gtk.Switch()
        autoplay_switch.set_valign(Gtk.Align.CENTER)
        autoplay_switch.set_active(self.settings.get_boolean("autoplay"))
        autoplay_switch.connect("notify::active", self.on_autoplay_changed)
        autoplay_row.add_suffix(autoplay_switch)
        behavior_group.add(autoplay_row)

        # Remember playback position
        remember_position_row = Adw.ActionRow()
        remember_position_row.set_title("Remember Position")
        remember_position_row.set_subtitle("Resume from last position when reopening songs")
        position_switch = Gtk.Switch()
        position_switch.set_valign(Gtk.Align.CENTER)
        position_switch.set_active(self.settings.get_boolean("remember-position"))
        position_switch.connect("notify::active", self.on_remember_position_changed)
        remember_position_row.add_suffix(position_switch)
        behavior_group.add(remember_position_row)

        # Gapless playback
        gapless_row = Adw.ActionRow()
        gapless_row.set_title("Gapless Playback")
        gapless_row.set_subtitle("Remove silence between tracks")
        gapless_switch = Gtk.Switch()
        gapless_switch.set_valign(Gtk.Align.CENTER)
        gapless_switch.set_active(self.settings.get_boolean("gapless-playback"))
        gapless_switch.connect("notify::active", self.on_gapless_changed)
        gapless_row.add_suffix(gapless_switch)
        behavior_group.add(gapless_row)

        # Interface page
        interface_page = Adw.PreferencesPage()
        interface_page.set_title("Interface")
        interface_page.set_icon_name("preferences-system-symbolic")
        self.add(interface_page)

        # Appearance group
        appearance_group = Adw.PreferencesGroup()
        appearance_group.set_title("Appearance")
        interface_page.add(appearance_group)

        # Show album art
        album_art_row = Adw.ActionRow()
        album_art_row.set_title("Show Album Art")
        album_art_row.set_subtitle("Display album artwork when available")
        album_art_switch = Gtk.Switch()
        album_art_switch.set_valign(Gtk.Align.CENTER)
        album_art_switch.set_active(self.settings.get_boolean("show-album-art"))
        album_art_switch.connect("notify::active", self.on_album_art_changed)
        album_art_row.add_suffix(album_art_switch)
        appearance_group.add(album_art_row)

        # Show time remaining
        time_remaining_row = Adw.ActionRow()
        time_remaining_row.set_title("Show Time Remaining")
        time_remaining_row.set_subtitle("Display remaining time instead of duration")
        time_remaining_switch = Gtk.Switch()
        time_remaining_switch.set_valign(Gtk.Align.CENTER)
        time_remaining_switch.set_active(self.settings.get_boolean("show-time-remaining"))
        time_remaining_switch.connect("notify::active", self.on_time_remaining_changed)
        time_remaining_row.add_suffix(time_remaining_switch)
        appearance_group.add(time_remaining_row)

    def on_autoplay_changed(self, switch, _):
        self.settings.set_boolean("autoplay", switch.get_active())

    def on_remember_position_changed(self, switch, _):
        self.settings.set_boolean("remember-position", switch.get_active())

    def on_gapless_changed(self, switch, _):
        self.settings.set_boolean("gapless-playback", switch.get_active())

    def on_album_art_changed(self, switch, _):
        self.settings.set_boolean("show-album-art", switch.get_active())

    def on_time_remaining_changed(self, switch, _):
        self.settings.set_boolean("show-time-remaining", switch.get_active())
