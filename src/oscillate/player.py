import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import time

class Player:
    def __init__(self, window):
        self.window = window
        self.current_file = None
        self.is_playing = False
        self.duration = 0
        self.volume = 1.0
        self.is_muted = False
        self.volume_before_mute = 1.0

        # Initialize GStreamer
        Gst.init(None)

        # Create playbin element
        self.playbin = Gst.ElementFactory.make('playbin', 'player')
        if not self.playbin:
            print("Error: Could not create playbin")
            return

        # Set initial volume
        self.playbin.set_property('volume', self.volume)

        # Create bus to get events from GStreamer pipeline
        bus = self.playbin.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

        # Connect controls
        self.window.song_progress_scale.connect('change-value', self.on_seek)
        self.window.volume_scale.connect('value-changed', self.on_volume_changed)
        self.window.mute_button.connect('clicked', self.on_mute_clicked)

        # Start position update timer
        GLib.timeout_add(200, self.update_position)

    def on_volume_changed(self, widget):
        """Handle volume slider changes"""
        self.volume = widget.get_value()
        self.playbin.set_property('volume', self.volume)

        # Update mute button icon based on volume level
        self.update_volume_icon()

    def on_mute_clicked(self, button):
        """Handle mute button clicks"""
        if self.is_muted:
            # Unmute
            self.is_muted = False
            self.playbin.set_property('volume', self.volume_before_mute)
            self.window.volume_scale.set_value(self.volume_before_mute)
        else:
            # Mute
            self.is_muted = True
            self.volume_before_mute = self.volume
            self.playbin.set_property('volume', 0)
            self.window.volume_scale.set_value(0)

        self.update_volume_icon()

    def update_volume_icon(self):
        """Update the volume button icon based on current volume state"""
        if self.is_muted or self.volume == 0:
            icon_name = "audio-volume-muted-symbolic"
        elif self.volume < 0.3:
            icon_name = "audio-volume-low-symbolic"
        elif self.volume < 0.7:
            icon_name = "audio-volume-medium-symbolic"
        else:
            icon_name = "audio-volume-high-symbolic"

        self.window.mute_button.set_icon_name(icon_name)

    def format_time(self, duration):
        if duration == 0:
            return "00:00"
        seconds = int(duration / Gst.SECOND)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


    def play(self, file_path=None):
        if file_path:
            self.current_file = file_path
            self.playbin.set_state(Gst.State.NULL)
            self.playbin.set_property('uri', f'file://{file_path}')

            # Reset labels and slider
            self.window.time_position_label.set_label("00:00")
            self.window.time_duration_label.set_label("00:00")
            self.window.song_progress_scale.set_value(0)

            # Restore volume settings for new track
            self.playbin.set_property('volume', 0 if self.is_muted else self.volume)

            # Query duration after a short delay
            GLib.timeout_add(100, self.query_duration)

        self.playbin.set_state(Gst.State.PLAYING)
        self.is_playing = True
        self.window.play_button.set_icon_name("media-playback-pause-symbolic")

    def pause(self):
        self.playbin.set_state(Gst.State.PAUSED)
        self.is_playing = False
        self.window.play_button.set_icon_name("media-playback-start-symbolic")

    def stop(self):
        self.playbin.set_state(Gst.State.NULL)
        self.is_playing = False
        self.window.play_button.set_icon_name("media-playback-start-symbolic")
        self.window.song_progress_scale.set_value(0)
        self.window.time_position_label.set_label("00:00")

    def toggle_playback(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def query_duration(self):
        success, duration = self.playbin.query_duration(Gst.Format.TIME)
        if success:
            self.duration = duration
            self.window.song_progress_scale.set_range(0, float(duration) / Gst.SECOND)
            duration_str = self.format_time(duration)
            self.window.time_duration_label.set_label(duration_str)
            return False
        return True

    def on_message(self, bus, message):
        t = message.type

        if t == Gst.MessageType.ERROR:
            self.playbin.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print(f"Error: {err}, {debug}")
            self.is_playing = False

        elif t == Gst.MessageType.EOS:
            # End of stream - play next track
            self.stop()
            self.window.play_next_track()

        elif t == Gst.MessageType.ASYNC_DONE:
            self.query_duration()

        elif t == Gst.MessageType.DURATION_CHANGED:
            # Get the duration
            success, self.duration = self.playbin.query_duration(Gst.Format.TIME)
            if success:
                # Convert to seconds
                self.duration = self.duration / Gst.SECOND
                self.window.song_progress_scale.set_range(0, self.duration)

    def update_position(self):
        if not self.is_playing:
            return True

        success, position = self.playbin.query_position(Gst.Format.TIME)
        if success:
            position_str = self.format_time(position)
            self.window.time_position_label.set_label(position_str)

            if self.duration > 0:
                value = float(position) / Gst.SECOND
                self.window.song_progress_scale.set_value(value)

        return True

    def on_seek(self, widget, scroll_type, value):
        if not self.is_playing or self.duration == 0:
            return False

        value = max(0, min(value, float(self.duration) / Gst.SECOND))
        position = value * Gst.SECOND

        position_str = self.format_time(position)
        self.window.time_position_label.set_label(position_str)

        # Perform seek
        self.playbin.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            position
        )

        return True
