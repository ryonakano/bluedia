#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")

import base64
import subprocess
import time
import requests
import json
import html
from gi.repository import Gtk, GLib, GdkPixbuf, Gdk

TOKEN_FILE_PATH = "spotify_token.json"
CACHE_DURATION = 3600
BLUETOOTH_UPDATE_INTERVAL = 2

class AlbumArtCache:
    def __init__(self):
        self.cache = {}
        self.last_track = None

    def get(self, track_id):
        if track_id in self.cache:
            url, timestamp = self.cache[track_id]
            if time.time() - timestamp < CACHE_DURATION:
                return url
            else:
                del self.cache[track_id]
        return None

    def set(self, track_id, url):
        self.cache[track_id] = (url, time.time())

def control_bluetooth(command, wait_after=0):
    try:
        print(f"DEBUG: Sending bluetoothctl command: {command}")
        process = subprocess.Popen(
            ['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        commands = f"menu player\n{command}\nshow"
        stdout, stderr = process.communicate(input=commands.encode())

        if wait_after > 0:
            time.sleep(wait_after)

        if stderr and "No default controller available" not in stderr.decode():
            print(f"DEBUG: Bluetoothctl error: {stderr.decode().strip()}")
        return stdout.decode()
    except Exception as e:
        print(f"DEBUG: Error interacting with bluetoothctl: {e}")
        return ""

def parse_track_details(output):
    track_details = {}
    for line in output.split("\n"):
        if "Track.Title" in line:
            track_details["Title"] = line.split(":")[-1].strip()
        elif "Track.Artist" in line:
            track_details["Artist"] = line.split(":")[-1].strip()
        elif "Track.Album" in line:
            track_details["Album"] = line.split(":")[-1].strip()
        elif "Status" in line:
            track_details["Status"] = line.split(":")[-1].strip()
        elif "Track.Duration" in line:
            try:
                hex_duration = line.split("(")[1].split(")")[0]
                track_details["Duration"] = int(hex_duration)
            except (ValueError, IndexError):
                track_details["Duration"] = 0
        elif "Position" in line:
            try:
                hex_pos = line.split("(")[1].split(")")[0]
                track_details["Position"] = int(hex_pos)
            except (ValueError, IndexError):
                track_details["Position"] = 0
    print("DEBUG: Parsed track details:", track_details)
    return track_details

def get_spotify_access_token(client_id, client_secret):
    print("DEBUG: Getting Spotify access token...")
    url = "https://accounts.spotify.com/api/token"
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode('ascii')).decode('ascii')

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials"
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        token = response.json().get("access_token")
        expires_in = response.json().get("expires_in", 3600)
        print("DEBUG: Got Spotify token.")
        return token, time.time() + expires_in
    else:
        print(f"DEBUG: Failed to get access token. Status code: {response.status_code}")
        return None, None

def fetch_album_art(track, artist, access_token):
    print("DEBUG: Fetching album art for:", track, artist)
    try:
        url = f"https://api.spotify.com/v1/search?q=track:{track}%20artist:{artist}&type=track"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data["tracks"]["items"]:
                album_art_url = data["tracks"]["items"][0]["album"]["images"][0]["url"]
                print("DEBUG: Album art found on Spotify:", album_art_url)
                return album_art_url
    except Exception as e:
        print(f"DEBUG: Error fetching album art: {e}")
    return None

def load_token():
    try:
        with open(TOKEN_FILE_PATH, 'r') as file:
            token_data = json.load(file)
            if token_data.get('expiry') and time.time() < token_data['expiry']:
                print("DEBUG: Loaded token from file.")
                return token_data['access_token'], token_data['expiry']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        print("DEBUG: No valid token found in file.")
    return None, None

def save_token(access_token, expiry):
    token_data = {
        "access_token": access_token,
        "expiry": expiry
    }
    with open(TOKEN_FILE_PATH, 'w') as file:
        json.dump(token_data, file)
    print("DEBUG: Token saved to file.")



def check_bluez_version():
    try:
        output = subprocess.check_output(['bluetoothctl', '--version'], text=True)
        version = output.strip().split()[-1]  # Gets the version number
        version_parts = [int(x) for x in version.split('.')]
        
        if version_parts[0] < 5 or (version_parts[0] == 5 and version_parts[1] < 70):
            print(f"Warning: This application requires bluez version 5.70 or higher. Found version {version}")
            print("Some features may not work correctly.")
    except Exception as e:
        print("Warning: Could not determine bluez version.")
        print("Please ensure you have bluez version 5.70 or higher installed.")

class BluetoothControlWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Bluedia")
        self.set_default_size(300, 400)

        self.last_track_details = {}
        self.access_token = None
        self.token_expiry = None
        self.shuffle_mode = False
        self.repeat_mode = "off"
        self.track_duration = 0
        self.is_playing = False
        self.album_art_cache = AlbumArtCache()
        self.no_player_available = False

        # For position timing:
        self.reported_position = 0
        self.last_update_time = time.time()

        # Flag to avoid scheduling updates repeatedly when a track has ended.
        self.track_ended_scheduled = False

        # For avoiding multiple pending updates.
        self.scheduled_update_id = None

        # CSS styling remains unchanged.
        css_provider = Gtk.CssProvider()
        css = """
            .rounded-image {
                border-radius: 20px;
                background-color: #333333;
            }
            .control-button {
                min-width: 30px;
                min-height: 30px;
                padding: 8px;
                border-radius: 15px;
                opacity: 0.8;
                background-color: rgba(255, 255, 255, 0.1);
            }
            .control-button:hover {
                background-color: rgba(255, 255, 255, 0.2);
                opacity: 1;
            }
            .control-button.active {
                color: #ff4081;
            }
            .progress-bar trough {
                min-height: 4px;
                border-radius: 2px;
            }
            .progress-bar highlight {
                min-height: 4px;
                border-radius: 2px;
                background-color: #ff4081;
            }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Main layout.
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        self.add(main_box)

        # --- Refresh button at the top right ---
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        top_box.set_halign(Gtk.Align.END)
        refresh_button = Gtk.Button()
        refresh_button.get_style_context().add_class('control-button')
        refresh_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        refresh_button.set_image(refresh_icon)
        refresh_button.connect("clicked", self.on_refresh_clicked)
        top_box.pack_start(refresh_button, False, False, 0)
        main_box.pack_start(top_box, False, True, 0)
        # -----------------------------------------

        # --- Album art area with overlay for loader ---
        album_art_center = Gtk.Box()
        album_art_center.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(album_art_center, False, True, 0)

        self.album_art_overlay = Gtk.Overlay()
        self.album_art_overlay.set_size_request(200, 200)
        album_art_center.pack_start(self.album_art_overlay, False, False, 0)

        self.album_art_image = Gtk.Image()
        self.album_art_overlay.add(self.album_art_image)

        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(200, 200)
        self.album_art_overlay.add_overlay(self.spinner)
        self.spinner.set_halign(Gtk.Align.CENTER)
        self.spinner.set_valign(Gtk.Align.CENTER)
        self.spinner.hide()
        # -----------------------------------------------

        # Track info.
        self.track_info_label = Gtk.Label()
        self.track_info_label.set_justify(Gtk.Justification.CENTER)
        self.track_info_label.set_line_wrap(True)
        self.track_info_label.set_max_width_chars(40)
        main_box.pack_start(self.track_info_label, False, True, 0)

        # Progress bar.
        progress_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(progress_box, False, True, 0)

        self.current_time_label = Gtk.Label(label="0:00")
        progress_box.pack_start(self.current_time_label, False, False, 0)
        
        self.progress_bar = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.progress_bar.set_draw_value(False)
        self.progress_bar.set_sensitive(False)
        self.progress_bar.get_style_context().add_class('progress-bar')
        self.progress_bar.set_size_request(200, 20)
        progress_box.pack_start(self.progress_bar, True, True, 0)
        
        self.total_time_label = Gtk.Label(label="0:00")
        progress_box.pack_start(self.total_time_label, False, False, 0)

        # Control buttons.
        button_box = Gtk.Box(spacing=30, orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(button_box, False, True, 20)

        button_configs = [
            ("media-playlist-shuffle-symbolic", self.on_shuffle_clicked, "shuffle_button"),
            ("media-skip-backward-symbolic", self.on_previous_clicked, None),
            ("media-playback-start-symbolic", self.on_play_pause_clicked, "play_pause_button"),
            ("media-skip-forward-symbolic", self.on_next_clicked, None),
            ("media-playlist-repeat-symbolic", self.on_repeat_clicked, "repeat_button")
        ]

        for icon_name, callback, attr_name in button_configs:
            button = Gtk.Button()
            button.get_style_context().add_class('control-button')
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
            button.set_image(icon)
            button.connect("clicked", callback)
            button_box.pack_start(button, False, False, 0)
            if attr_name:
                setattr(self, attr_name, button)
                setattr(self, f"{attr_name}_icon", icon)

        # Enable dark theme.
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)

        # Start timers.
        self.update_track_info(force=True)
        GLib.timeout_add(500, self.update_progress)
        GLib.timeout_add_seconds(1, self.increment_position)

    # --- Loader methods ---
    def show_loader(self):
        print("DEBUG: Starting loader spinner")
        self.spinner.show()
        self.spinner.start()
        # Process pending events so that the spinner is drawn immediately.
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)

    def hide_loader(self):
        print("DEBUG: Stopping loader spinner")
        self.spinner.stop()
        self.spinner.hide()

    # --- Helper for scheduling a one-shot forced update ---
    def schedule_update(self, force=True):
        print(f"DEBUG: Scheduling update in 1 seconds (force={force})")
        if self.scheduled_update_id is not None:
            GLib.source_remove(self.scheduled_update_id)
            self.scheduled_update_id = None
        self.scheduled_update_id = GLib.timeout_add_seconds(1, self.delayed_update, force)

    def delayed_update(self, force):
        self.scheduled_update_id = None
        self.update_track_info(force)
        return False  # one-shot callback

    # -----------------------------------------

    def format_time(self, milliseconds):
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def increment_position(self):
        if self.is_playing and not self.no_player_available:
            elapsed_ms = (time.time() - self.last_update_time) * 1000
            self.current_position = self.reported_position + int(elapsed_ms)
            if self.current_position >= self.track_duration:
                self.current_position = self.track_duration
                # Only schedule a forced update once per track end.
                if not self.track_ended_scheduled:
                    self.schedule_update(force=True)
                    self.track_ended_scheduled = True
        return True

    def update_progress(self):
        if self.track_duration > 0:
            progress = (self.current_position / self.track_duration) * 100
            self.progress_bar.set_value(progress)
            self.current_time_label.set_text(self.format_time(self.current_position))
            self.total_time_label.set_text(self.format_time(self.track_duration))
        return True

    def set_fallback_image(self):
        print("DEBUG: Setting fallback image")
        response = requests.get(
            'https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/eb777e7a-7d3c-487e-865a-fc83920564a1/d7kpm65-437b2b46-06cd-4a86-9041-cc8c3737c6f0.jpg/v1/fill/w_800,h_800,q_75,strp/no_album_art__no_cover___placeholder_picture_by_cmdrobot_d7p65-fullview.jpg?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9ODAwIiwicGF0aCI6IlwvZlwvZWI3NzdlN2EtN2QzYy00ODdlLTg2NWEtZmM4MzkyMDU2NGExXC9kN2twbTY1LTQzN2IyYjQ2LTA2Y2QtNGE4Ni05MDQxLWNjOGMzNzM3YzZmMC5qcGciLCJ3aWR0aCI6Ijw9ODAwIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmltYWdlLm9wZXJhdGlvbnMiXX0.8yjX5CrFjxVH06LB59TpJLu6doZb0wz8fGQq4tM64mg'
        )
        loader = GdkPixbuf.PixbufLoader()
        loader.write(response.content)
        loader.close()
        pixbuf = loader.get_pixbuf()
        scaled_pixbuf = pixbuf.scale_simple(200, 200, GdkPixbuf.InterpType.BILINEAR)
        self.album_art_image.set_from_pixbuf(scaled_pixbuf)
        self.hide_loader()

    def show_error_dialog(self, message):
        print("DEBUG: Showing error dialog:", message)
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

    def update_track_info(self, force=False):
        print("DEBUG: update_track_info called with force =", force)
        if force:
            self.show_loader()

        # If not forced and no update condition, exit.
        if not force and not (self.current_position >= self.track_duration or self.no_player_available):
            self.hide_loader()
            return True

        if not self.access_token or time.time() >= self.token_expiry:
            self.access_token, self.token_expiry = load_token()
            if not self.access_token or time.time() >= self.token_expiry:
                self.access_token, self.token_expiry = get_spotify_access_token(
                    "d2f2518919d845278340acdc1dd80db2",
                    "573be4444ec449a1a559e945f48e3d01"
                )
                if self.access_token:
                    save_token(self.access_token, self.token_expiry)

        print("DEBUG: Fetching track details from bluetooth")
        output = control_bluetooth("show")
        track_details = parse_track_details(output)

        # Check if no device is connected.
        if "No default player available" in output:
            self.track_info_label.set_markup(
                "<span size='large'><b>No media player found</b></span>\nPlease connect one"
            )
            self.set_fallback_image()
            for button in [self.shuffle_button, self.repeat_button]:
                button.set_sensitive(False)
            self.progress_bar.set_value(0)
            self.current_time_label.set_text("0:00")
            self.total_time_label.set_text("0:00")
            self.no_player_available = True
            self.hide_loader()
            return True
        else:
            for button in [self.shuffle_button, self.repeat_button]:
                button.set_sensitive(True)
        self.no_player_available = False

        if (track_details.get('Title', '') in ['Not Provided', ''] and 
            track_details.get('Artist', '') in ['Not Provided', '']):
            self.track_info_label.set_markup(
                "<span size='large'><b>No media is playing</b></span>\nClick play to start"
            )
            self.set_fallback_image()
            for button in [self.play_pause_button, self.shuffle_button, self.repeat_button]:
                button.set_sensitive(True)
            self.progress_bar.set_value(0)
            self.current_time_label.set_text("0:00")
            self.total_time_label.set_text("0:00")
            self.hide_loader()
            return True

        # Update details if track info has changed or forced.
        if track_details != self.last_track_details or force:
            self.last_track_details = track_details
            # Reset the "track ended" flag.
            self.track_ended_scheduled = False
            self.reported_position = track_details.get("Position", 0)
            self.last_update_time = time.time()
            self.current_position = self.reported_position
            self.track_duration = track_details.get("Duration", 0)
            self.is_playing = track_details.get("Status", "").lower() == "playing"

            title = html.escape(track_details.get('Title', 'Unknown'))
            artist = html.escape(track_details.get('Artist', 'Unknown'))
            track_info = f"<span size='x-large'><b>{title}</b></span>\n{artist}"
            self.track_info_label.set_markup(track_info)

            self.play_pause_button_icon.set_from_icon_name(
                "media-playback-pause-symbolic" if self.is_playing else "media-playback-start-symbolic",
                Gtk.IconSize.LARGE_TOOLBAR
            )

            if "Shuffle: alltracks" in output:
                self.shuffle_mode = True
                self.shuffle_button.get_style_context().add_class('active')
            else:
                self.shuffle_mode = False
                self.shuffle_button.get_style_context().remove_class('active')

            repeat_mode = "off"
            if "Repeat: alltracks" in output:
                repeat_mode = "alltracks"
            elif "Repeat: singletrack" in output:
                repeat_mode = "singletrack"
            self.repeat_mode = repeat_mode

            if repeat_mode == "alltracks":
                self.repeat_button_icon.set_from_icon_name("media-playlist-repeat-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
                self.repeat_button.get_style_context().add_class('active')
            elif repeat_mode == "singletrack":
                self.repeat_button_icon.set_from_icon_name("media-playlist-repeat-one-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
                self.repeat_button.get_style_context().add_class('active')
            else:
                self.repeat_button_icon.set_from_icon_name("media-playlist-repeat-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
                self.repeat_button.get_style_context().remove_class('active')

            # Fetch album art.
            track_id = f"{title}-{artist}"
            cached_url = self.album_art_cache.get(track_id)
            if cached_url:
                print("DEBUG: Loading album art from cache")
                response = requests.get(cached_url)
                loader = GdkPixbuf.PixbufLoader()
                loader.write(response.content)
                loader.close()
                pixbuf = loader.get_pixbuf()
                scaled_pixbuf = pixbuf.scale_simple(200, 200, GdkPixbuf.InterpType.BILINEAR)
                self.album_art_image.set_from_pixbuf(scaled_pixbuf)
            elif self.access_token and track_id != self.album_art_cache.last_track:
                print("DEBUG: Fetching new album art from Spotify")
                self.album_art_cache.last_track = track_id
                album_art_url = fetch_album_art(title, artist, self.access_token)
                if album_art_url:
                    self.album_art_cache.set(track_id, album_art_url)
                    response = requests.get(album_art_url)
                    loader = GdkPixbuf.PixbufLoader()
                    loader.write(response.content)
                    loader.close()
                    pixbuf = loader.get_pixbuf()
                    scaled_pixbuf = pixbuf.scale_simple(200, 200, GdkPixbuf.InterpType.BILINEAR)
                    self.album_art_image.set_from_pixbuf(scaled_pixbuf)
                else:
                    self.set_fallback_image()
        self.hide_loader()
        return True

    def on_play_pause_clicked(self, widget):
        print("DEBUG: Play/Pause button clicked")
        if self.no_player_available:
            self.show_error_dialog("No media player connected. Please connect a device first.")
            return
        if self.is_playing:
            control_bluetooth("pause")
            self.play_pause_button_icon.set_from_icon_name("media-playback-start-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            self.is_playing = False
        else:
            control_bluetooth("play")
            self.play_pause_button_icon.set_from_icon_name("media-playback-pause-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            self.is_playing = True
        self.schedule_update(force=True)

    def on_next_clicked(self, widget):
        print("DEBUG: Next button clicked")
        if self.no_player_available:
            self.show_error_dialog("No media player connected. Please connect a device first.")
            return
        control_bluetooth("next")
        self.schedule_update(force=True)

    def on_previous_clicked(self, widget):
        print("DEBUG: Previous button clicked")
        if self.no_player_available:
            self.show_error_dialog("No media player connected. Please connect a device first.")
            return
        # Use your modified logic (simply call "previous")
        control_bluetooth("previous")
        self.schedule_update(force=True)

    def on_shuffle_clicked(self, widget):
        print("DEBUG: Shuffle button clicked")
        if self.no_player_available:
            self.show_error_dialog("No media player connected. Please connect a device first.")
            return
        self.shuffle_mode = not self.shuffle_mode
        control_bluetooth("shuffle alltracks" if self.shuffle_mode else "shuffle off")
        if self.shuffle_mode:
            self.shuffle_button.get_style_context().add_class('active')
        else:
            self.shuffle_button.get_style_context().remove_class('active')
        self.schedule_update(force=True)

    def on_repeat_clicked(self, widget):
        print("DEBUG: Repeat button clicked")
        if self.no_player_available:
            self.show_error_dialog("No media player connected. Please connect a device first.")
            return
        modes = {"off": "alltracks", "alltracks": "singletrack", "singletrack": "off"}
        self.repeat_mode = modes[self.repeat_mode]
        control_bluetooth(f"repeat {self.repeat_mode}")
        
        if self.repeat_mode == "alltracks":
            self.repeat_button_icon.set_from_icon_name("media-playlist-repeat-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            self.repeat_button.get_style_context().add_class('active')
        elif self.repeat_mode == "singletrack":
            self.repeat_button_icon.set_from_icon_name("media-playlist-repeat-one-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            self.repeat_button.get_style_context().add_class('active')
        else:
            self.repeat_button_icon.set_from_icon_name("media-playlist-repeat-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            self.repeat_button.get_style_context().remove_class('active')
        
        self.schedule_update(force=True)

    def on_refresh_clicked(self, widget):
        print("DEBUG: Refresh button clicked")
        self.show_loader()
        self.schedule_update(force=True)

def main():
    # Add this at the start of your main() function
    check_bluez_version()
    window = BluetoothControlWindow()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    window.queue_draw()
    Gtk.main()

if __name__ == "__main__":
    main()
