"""
Oscillate Media Player - Main Window Implementation
This module contains the main window and song row implementations for the Oscillate media player.
"""

from gi.repository import Adw, Gtk, Gdk, Gio, GLib, Pango
from pathlib import Path
from typing import Optional, Any
import logging
from .player import Player

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from mutagen.mp3 import MP3
    from mutagen.easyid3 import EasyID3
    HAVE_MUTAGEN = True
except ImportError:
    HAVE_MUTAGEN = False
    logger.warning("Mutagen not found. Limited metadata support available.")

class SongRow(Gtk.ListBoxRow):
    """A custom ListBoxRow that represents a song in the playlist."""

    def __init__(self, title: str, artist: str, file_path: str):
        super().__init__()
        self.file_path = file_path
        self.active_popover: Optional[Gtk.PopoverMenu] = None

        # Create layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        vbox.set_margin_start(6)
        vbox.set_margin_end(6)
        vbox.set_margin_top(6)
        vbox.set_margin_bottom(6)

        # Song title with ellipsis
        title_label = Gtk.Label(label=title)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_ellipsize(Pango.EllipsizeMode.END)
        title_label.add_css_class("heading")
        vbox.append(title_label)

        # Artist name with ellipsis
        artist_label = Gtk.Label(label=artist)
        artist_label.set_halign(Gtk.Align.START)
        artist_label.set_ellipsize(Pango.EllipsizeMode.END)
        artist_label.add_css_class("caption")
        artist_label.add_css_class("dim-label")
        vbox.append(artist_label)

        self.select_check = Gtk.CheckButton()
        self.select_check.set_css_classes(['circular'])
        self.select_check.set_visible(False)

        self.set_child(vbox)

    def cleanup(self) -> None:
        """Clean up any attached widgets before removal."""
        if self.active_popover:
            self.active_popover.unparent()
            self.active_popover = None

@Gtk.Template(resource_path='/com/example/Oscillate/window.ui')
class OscillateWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'OscillateWindow'

    select_all_button = Gtk.Template.Child()
    songs_list_box = Gtk.Template.Child()
    headerbar = Gtk.Template.Child()
    play_button = Gtk.Template.Child()
    previous_button = Gtk.Template.Child()
    next_button = Gtk.Template.Child()
    song_progress_scale = Gtk.Template.Child()
    time_position_label = Gtk.Template.Child()
    time_duration_label = Gtk.Template.Child()
    overlay_split_view = Gtk.Template.Child()
    toggle_sidebar_button = Gtk.Template.Child()
    content_box = Gtk.Template.Child()
    album_picture = Gtk.Template.Child()
    song_title_label = Gtk.Template.Child()
    artist_name_label = Gtk.Template.Child()
    volume_scale = Gtk.Template.Child()
    mute_button = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    delete_revealer = Gtk.Template.Child()
    cancel_delete_button = Gtk.Template.Child()
    confirm_delete_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()
    search_revealer = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    search_button = Gtk.Template.Child()

    select_all_button.connect('clicked', on_select_all)
    selection_mode = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.selection_mode = None

        self.select_all_button.connect('clicked', self.on_select_all)

        # Initialize state
        self.player = Player(self)
        self.current_song_index = -1

        # Initialize settings
        self.settings = Gio.Settings.new("com.example.Oscillate")

        # Connect signals
        self.toggle_sidebar_button.connect('toggled', self.on_sidebar_button_toggled)
        self.songs_list_box.connect('row-activated', self.on_song_activated)
        self.play_button.connect('clicked', self.on_play_clicked)
        self.next_button.connect('clicked', self.on_next_clicked)
        self.previous_button.connect('clicked', self.on_previous_clicked)
        self.mute_button.connect('clicked', self.on_mute_clicked)
        self.volume_scale.connect('value-changed', self.on_volume_changed)

        self.delete_button.connect('clicked', self.on_delete_button_clicked)
        self.cancel_delete_button.connect('clicked', self.on_cancel_delete)
        self.confirm_delete_button.connect('clicked', self.on_confirm_delete)

        self.search_button.connect('toggled', self.on_search_toggled)
        self.search_entry.connect('search-changed', self.on_search_changed)

        # Set up initial state
        self.songs_list_box.set_selection_mode(Gtk.SelectionMode.MULTIPLE)

        # Add open button to header bar
        open_button = Gtk.Button(icon_name="folder-music-symbolic")
        open_button.set_tooltip_text("Open Music Files")
        open_button.connect('clicked', self.on_open_button_clicked)
        self.headerbar.pack_start(open_button)

        if not HAVE_MUTAGEN:
            self.show_mutagen_missing_warning()

    def on_search_toggled(self, button):
        is_active = button.get_active()
        self.search_revealer.set_reveal_child(is_active)

        # Clear search when closing
        if not is_active:
            self.search_entry.set_text("")
            self.filter_playlist("")

    def on_search_changed(self, entry):
        query = entry.get_text().strip().lower()
        self.filter_playlist(query)

    def filter_playlist(self, query):
        row = self.songs_list_box.get_first_child()
        while row:
            title_label = row.get_child().get_first_child()
            artist_label = row.get_child().get_last_child()

            title = title_label.get_label().lower()
            artist = artist_label.get_label().lower()

            visible = query in title or query in artist
            row.set_visible(visible)

            if not visible and row.is_selected():
                self.songs_list_box.unselect_row(row)

            row = row.get_next_sibling()

    def show_toast(self, message: str):
        """Show a toast notification."""
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

    def on_key_pressed(self, controller: Gtk.EventControllerKey,
                  keyval: int, keycode: int, state: Gdk.ModifierType) -> bool:
        """Handle keyboard shortcuts."""
        if isinstance(self.get_focus(), Gtk.Entry):
            return False

        key_name = Gdk.keyval_name(keyval)

        if key_name == "space":
            self.play_button.emit('clicked')
            return True
        elif key_name == "Left":
            self.previous_button.emit('clicked')
            return True
        elif key_name == "Right":
            self.next_button.emit('clicked')
            return True
        elif key_name == "m":
            self.mute_button.emit('clicked')
            return True
        elif key_name == "Up":
            current = self.volume_scale.get_value()
            self.volume_scale.set_value(min(1.0, current + 0.05))
            return True
        elif key_name == "Down":
            current = self.volume_scale.get_value()
            self.volume_scale.set_value(max(0.0, current - 0.05))
            return True
        elif key_name == "F9":
            self.toggle_sidebar_button.set_active(
                not self.toggle_sidebar_button.get_active()
            )
            return True
        elif key_name == "Delete":
            self.delete_selected_song()
            return True

        return False

    def on_delete_button_clicked(self, button):
        self.delete_revealer.set_reveal_child(True)

    def on_cancel_delete(self, button):
        self.delete_revealer.set_reveal_child(False)

    def on_confirm_delete(self, button):
        selected_rows = self.get_selected_rows()

        if not selected_rows:
            self.delete_revealer.set_reveal_child(False)
            return

        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=f"Delete {len(selected_rows)} song{'s' if len(selected_rows) > 1 else ''}?",
            body="This will permanently remove the selected songs from the playlist.",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)

        def on_response(dialog, response):
            if response == "delete":
                self.perform_delete(selected_rows)
            self.delete_revealer.set_reveal_child(False)
            dialog.destroy()

        dialog.connect("response", on_response)
        dialog.present()

    def get_selected_rows(self):
        selected_rows = []
        row = self.songs_list_box.get_first_child()
        while row:
            if row.is_selected():
                selected_rows.append(row)
            row = row.get_next_sibling()
        return selected_rows


    def on_delete_request(self):
        """Handle delete request from menu or keyboard."""
        self.delete_selected_song()

    def delete_selected_song(self, *args: Any) -> None:
        selected_rows = []
        row = self.songs_list_box.get_first_child()
        while row:
            if row.is_selected():
                selected_rows.append(row)
            row = row.get_next_sibling()

        if not selected_rows:
            return

        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=f"Delete {len(selected_rows)} selected song{'s' if len(selected_rows) > 1 else ''}?",
            body="This action cannot be undone."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", lambda d, r: self.perform_delete(selected_rows) if r == "delete" else None)
        dialog.present()

    def perform_delete(self, rows_to_delete: list):
        try:
            current_index = self.current_song_index
            deleted_indexes = [row.get_index() for row in rows_to_delete]

            for row in sorted(rows_to_delete, key=lambda r: r.get_index(), reverse=True):
                if row.get_index() == current_index:
                    self.player.stop()
                    self.current_song_index = -1
                    self.update_now_playing_labels()

                self.songs_list_box.remove(row)

            if self.current_song_index != -1:
                num_deleted_before = sum(1 for i in deleted_indexes if i < self.current_song_index)
                self.current_song_index -= num_deleted_before

            self.show_toast(f"Removed {len(rows_to_delete)} song{'s' if len(rows_to_delete) > 1 else ''}")

        except Exception as e:
            logger.error(f"Deletion failed: {e}")
            self.show_error_dialog("Deletion Error", str(e))

    def update_now_playing_labels(self):
        self.song_title_label.set_label("No song playing")
        self.artist_name_label.set_label("Select a song to play")

    def setup_controllers(self):
        """Set up keyboard and mouse controllers."""
        key_controller = Gtk.EventControllerKey()
        key_controller.connect('key-pressed', self.on_key_pressed)
        self.add_controller(key_controller)

    def setup_toast_overlay(self):
        """Set up the toast overlay properly."""
        main_box = self.get_content()
        if main_box:
            main_box.unparent()
            self.toast_overlay = Adw.ToastOverlay()
            self.toast_overlay.set_child(main_box)
            self.set_content(self.toast_overlay)


    def on_open_button_clicked(self, button: Gtk.Button) -> None:
        """Handle click on the open button."""
        dialog = Gtk.FileChooserDialog(
            title="Choose MP3 Files",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )

        dialog.add_buttons(
            "Cancel",
            Gtk.ResponseType.CANCEL,
            "Open",
            Gtk.ResponseType.ACCEPT,
        )

        file_filter = Gtk.FileFilter()
        file_filter.set_name("MP3 files")
        file_filter.add_mime_type("audio/mpeg")
        dialog.add_filter(file_filter)

        dialog.set_select_multiple(True)
        dialog.connect('response', self.on_file_dialog_response)
        dialog.present()

    def on_file_dialog_response(self, dialog: Gtk.FileChooserDialog,
                              response: Gtk.ResponseType) -> None:
        """Handle response from file chooser dialog."""
        try:
            if response == Gtk.ResponseType.ACCEPT:
                files = dialog.get_files()

                # Store initial state
                had_songs = self.songs_list_box.get_first_child() is not None

                # Add all files
                for file in files:
                    self.add_song_from_file(file.get_path())

                # Show summary toast if multiple files were added
                if len(files) > 1:
                    toast = Adw.Toast.new(f"Added {len(files)} songs to playlist")
                    toast.set_timeout(3)
                    self.toast_overlay.add_toast(toast)
        finally:
            dialog.destroy()

    def add_song_from_file(self, file_path: str) -> None:
        """Add a song to the playlist from a file path."""
        try:
            if HAVE_MUTAGEN:
                audio = MP3(file_path, ID3=EasyID3)
                title = audio.get('title', [Path(file_path).stem])[0]
                artist = audio.get('artist', ['Unknown Artist'])[0]
            else:
                title = Path(file_path).stem
                artist = 'Unknown Artist'

            row = SongRow(title, artist, file_path)
            self.songs_list_box.append(row)

            # Check if we should auto-play
            should_autoplay = self.settings.get_boolean("autoplay")
            is_first_song = self.songs_list_box.get_first_child() == row
            no_song_playing = self.current_song_index == -1

            if should_autoplay and is_first_song and no_song_playing:
                toast = Adw.Toast.new(f"Auto-playing: {title}")
                toast.set_timeout(3)  # 3 seconds
                self.toast_overlay.add_toast(toast)

                # Start playing the first song
                GLib.idle_add(self.start_autoplay, row)

        except Exception as e:
            logger.error(f"Error adding song {file_path}: {e}")
            self.show_error_dialog(
                "Error Adding Song",
                f"Could not add {Path(file_path).name}: {str(e)}"
            )

    def start_autoplay(self, row: SongRow) -> bool:
        """Start playing a song (called from idle)."""
        self.current_song_index = 0
        self.on_song_activated(self.songs_list_box, row)
        return False

    def on_play_clicked(self, button: Gtk.Button) -> None:
        """Handle play button clicks."""
        if self.current_song_index < 0:
            # No song selected, play first song if available
            first_row = self.songs_list_box.get_first_child()
            if first_row:
                self.current_song_index = 0
                self.on_song_activated(self.songs_list_box, first_row)
        else:
            self.player.toggle_playback()

    def on_next_clicked(self, button: Gtk.Button) -> None:
        """Handle next button clicks."""
        self.play_next_track()

    def on_previous_clicked(self, button: Gtk.Button) -> None:
        """Handle previous button clicks."""
        self.play_previous_track()

    def play_next_track(self) -> None:
        """Play the next track in the playlist."""
        if self.current_song_index >= 0:
            next_index = self.current_song_index + 1
            row = self.songs_list_box.get_row_at_index(next_index)
            if row:
                self.current_song_index = next_index
                self.on_song_activated(self.songs_list_box, row)

    def play_previous_track(self) -> None:
        """Play the previous track in the playlist."""
        if self.current_song_index > 0:
            prev_index = self.current_song_index - 1
            row = self.songs_list_box.get_row_at_index(prev_index)
            if row:
                self.current_song_index = prev_index
                self.on_song_activated(self.songs_list_box, row)

    def on_song_activated(self, list_box: Gtk.ListBox, row: SongRow) -> None:
        """Handle song selection."""
        self.current_song_index = row.get_index()
        title_label = row.get_child().get_first_child()
        artist_label = row.get_child().get_last_child()
        self.song_title_label.set_label(title_label.get_label())
        self.artist_name_label.set_label(artist_label.get_label())
        self.player.play(row.file_path)

    def on_mute_clicked(self, button: Gtk.Button) -> None:
        """Handle mute button clicks."""
        self.player.on_mute_clicked(button)

    def on_volume_changed(self, scale: Gtk.Scale) -> None:
        """Handle volume slider changes."""
        self.player.on_volume_changed(scale)

    def on_sidebar_button_toggled(self, button: Gtk.ToggleButton) -> None:
        """Handle sidebar toggle button clicks."""
        self.overlay_split_view.set_show_sidebar(button.get_active())
        icon_name = "sidebar-hide-symbolic" if button.get_active() else "sidebar-show-symbolic"
        button.set_icon_name(icon_name)

    def show_error_dialog(self, title: str, message: str) -> None:
        """Show an error dialog to the user."""
        dialog = Adw.MessageDialog.new(
            self,
            title,
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def show_mutagen_missing_warning(self) -> None:
        """Show warning about missing mutagen dependency."""
        dialog = Adw.MessageDialog.new(
            self,
            "Missing Dependency",
            "The python-mutagen package is required for reading music metadata. "
            "Basic playback will still work, but song information may be limited."
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def delete_selected_song(self, *args: Any) -> None:
        """Delete the selected song from the playlist."""
        selected_row = self.songs_list_box.get_selected_row()
        if not selected_row or not isinstance(selected_row, SongRow):
            return

        # Clean up any active popover first
        if hasattr(selected_row, 'cleanup'):
            selected_row.cleanup()

        title = selected_row.get_child().get_first_child().get_label()
        artist = selected_row.get_child().get_last_child().get_label()

        dialog = Adw.MessageDialog.new(
            self,
            f'Delete "{title}"?',
            f'Are you sure you want to remove "{title}" by {artist} from the playlist?'
        )

        # Add buttons
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)

        # Set default response
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")

        def on_response(dialog: Adw.MessageDialog, response: str) -> None:
            try:
                if response == "delete":
                    row_index = selected_row.get_index()

                    # If this is the currently playing song, stop playback
                    if self.current_song_index == row_index:
                        self.player.stop()
                        self.current_song_index = -1
                        self.song_title_label.set_label("No song playing")
                        self.artist_name_label.set_label("Select a song to play")

                    # Remove the row
                    self.songs_list_box.remove(selected_row)

                    # Update current_song_index if needed
                    if self.current_song_index > row_index:
                        self.current_song_index -= 1

                    # Show deletion toast
                    self.show_toast(f"Removed: {title}")
            finally:
                dialog.destroy()

        # Connect response signal and show dialog
        dialog.connect("response", on_response)
        dialog.present()

    def on_popover_closed(self, popover: Gtk.PopoverMenu, row: SongRow) -> None:
        """Handle cleanup when a popover is closed."""
        if row.active_popover == popover:
            row.active_popover = None
            popover.unparent()

    def on_select_all(self, button):
        self.selection_mode = not self.selection_mode
        icon = 'checkbox-checked-symbolic' if self.selection_mode else 'checkbox-empty-symbolic'
        self.select_all_button.set_icon_name(icon)

        row = self.songs_list_box.get_first_child()
        while row:
            checkbox = row.get_child().get_first_child()
            checkbox.set_visible(self.selection_mode)
            checkbox.set_active(self.selection_mode)
            row = row.get_next_sibling()

    def toggle_selection_ui(self, enable):
        animation = Adw.TimedAnimation(
            widget=self.songs_list_box,
            value_from=self.songs_list_box.get_margin_start(),
            value_to=12 if enable else 0,
            duration=200,
            easing=Adw.Easing.LINEAR
        )
        animation.connect('done', lambda *_: None)
        animation.play()
