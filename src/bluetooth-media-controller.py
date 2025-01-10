import gi
gi.require_version("Gtk", "3.0")

import base64
import subprocess
import time
import requests
import json
import html
from gi.repository import Gtk, GLib, GdkPixbuf, Gdk

# Path to store the token details in a file
TOKEN_FILE_PATH = "spotify_token.json"
CACHE_DURATION = 3600  # Cache duration in seconds

def create_window_icon():
    try:
        with open('/usr/local/share/icons/hicolor/128x128/apps/bluetooth-media-controller.png', 'rb') as file:
            icon_bytes = file.read()
        loader = GdkPixbuf.PixbufLoader()
        loader.write(icon_bytes)
        loader.close()
        return loader.get_pixbuf()
    except Exception as e:
        print("Error in creating icon:", e)
        return None

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
        process = subprocess.Popen(
            ['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        commands = f"menu player\n{command}\nshow"
        stdout, stderr = process.communicate(input=commands.encode())

        if wait_after > 0:
            time.sleep(wait_after)

        if stderr and "No default controller available" not in stderr.decode():
            print(f"Bluetoothctl error: {stderr.decode().strip()}")
        return stdout.decode()
    except Exception as e:
        print(f"Error interacting with bluetoothctl: {e}")
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
    return track_details

def get_spotify_access_token(client_id, client_secret):
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
        return token, time.time() + expires_in
    else:
        print(f"Failed to get access token. Status code: {response.status_code}")
        return None, None

def fetch_album_art(track, artist, access_token):
    try:
        url = f"https://api.spotify.com/v1/search?q=track:{track}%20artist:{artist}&type=track"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data["tracks"]["items"]:
                return data["tracks"]["items"][0]["album"]["images"][0]["url"]
    except Exception as e:
        print(f"Error fetching album art: {e}")
    return None

def load_token():
    try:
        with open(TOKEN_FILE_PATH, 'r') as file:
            token_data = json.load(file)
            if token_data.get('expiry') and time.time() < token_data['expiry']:
                return token_data['access_token'], token_data['expiry']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return None, None

def save_token(access_token, expiry):
    token_data = {
        "access_token": access_token,
        "expiry": expiry
    }
    with open(TOKEN_FILE_PATH, 'w') as file:
        json.dump(token_data, file)

class BluetoothControlWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Bluetooth Media Controller")
        self.set_default_size(300, 400)
        
        # Set the window icon
        icon = create_window_icon()
        if icon:
            self.set_icon(icon)

        self.last_track_details = {}
        self.access_token = None
        self.token_expiry = None
        self.shuffle_mode = False
        self.repeat_mode = "off"
        self.current_position = 0
        self.track_duration = 0
        self.album_art_cache = AlbumArtCache()

        # Set up CSS styling
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

        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        self.add(main_box)

        # Center-aligned container for album art
        album_art_center = Gtk.Box()
        album_art_center.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(album_art_center, False, True, 0)

        # Album art with rounded corners
        self.album_art_container = Gtk.Box()
        self.album_art_container.get_style_context().add_class('rounded-image')
        self.album_art_image = Gtk.Image()
        self.album_art_image.set_size_request(200, 200)
        self.album_art_container.add(self.album_art_image)
        album_art_center.add(self.album_art_container)

        # Track info
        self.track_info_label = Gtk.Label()
        self.track_info_label.set_justify(Gtk.Justification.CENTER)
        self.track_info_label.set_line_wrap(True)
        self.track_info_label.set_max_width_chars(40)
        main_box.pack_start(self.track_info_label, False, True, 0)

        # Progress bar and time labels
        progress_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(progress_box, False, True, 0)

        self.current_time_label = Gtk.Label(label="0:00")
        progress_box.pack_start(self.current_time_label, False, False, 0)
        
        self.progress_bar = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.progress_bar.set_draw_value(False)
        self.progress_bar.set_sensitive(False)  # Disable seeking
        self.progress_bar.get_style_context().add_class('progress-bar')
        self.progress_bar.set_size_request(200, 20)
        progress_box.pack_start(self.progress_bar, True, True, 0)
        
        self.total_time_label = Gtk.Label(label="0:00")
        progress_box.pack_start(self.total_time_label, False, False, 0)

        # Control buttons
        button_box = Gtk.Box(spacing=30, orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.CENTER)
        main_box.pack_start(button_box, False, True, 20)

        # Create buttons with symbolic icons
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

        # Enable dark theme
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)

        # Start update timers
        self.update_track_info()
        GLib.timeout_add(500, self.update_progress)
        GLib.timeout_add_seconds(1, self.update_track_info)

    def format_time(self, milliseconds):
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def update_progress(self):
        output = control_bluetooth("show")
        track_details = parse_track_details(output)
        
        if track_details.get("Duration", 0) > 0:
            position = track_details.get("Position", 0)
            duration = track_details.get("Duration", 0)
            
            progress = (position / duration) * 100
            self.progress_bar.set_value(progress)
            self.current_time_label.set_text(self.format_time(position))
            self.total_time_label.set_text(self.format_time(duration))
            
            if position >= duration:
                self.update_track_info()
        
        return True

    def set_fallback_image(self):
        response = requests.get('https://img.freepik.com/free-vector/oops-404-error-with-broken-robot-concept-illustration_114360-5529.jpg')
        loader = GdkPixbuf.PixbufLoader()
        loader.write(response.content)
        loader.close()
        pixbuf = loader.get_pixbuf()
        scaled_pixbuf = pixbuf.scale_simple(200, 200, GdkPixbuf.InterpType.BILINEAR)
        self.album_art_image.set_from_pixbuf(scaled_pixbuf)

    def show_error_dialog(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()

    def update_track_info(self):
        if not self.access_token or time.time() >= self.token_expiry:
            self.access_token, self.token_expiry = load_token()
            if not self.access_token or time.time() >= self.token_expiry:
                self.access_token, self.token_expiry = get_spotify_access_token(
                    "d2f2518919d845278340acdc1dd80db2",
                    "573be4444ec449a1a559e945f48e3d01"
                )
                if self.access_token:
                    save_token(self.access_token, self.token_expiry)

        output = control_bluetooth("show")
        track_details = parse_track_details(output)

        # Check for no device connected
        if "No default player available" in output:
            self.track_info_label.set_markup(
                "<span size='large'><b>No media player found</b></span>\n" +
                "Please connect one"
            )
            self.set_fallback_image()
            # Disable all playback control buttons
            for button in [self.shuffle_button, 
                        self.repeat_button]:
                button.set_sensitive(False)
            self.progress_bar.set_value(0)
            self.current_time_label.set_text("0:00")
            self.total_time_label.set_text("0:00")
            self.no_player_available = True  # Add this flag
            return True
        else:
            for button in [self.shuffle_button, 
                        self.repeat_button]:
                button.set_sensitive(True)

        track_details = parse_track_details(output)
        self.no_player_available = False  # Reset flag when player is available

        # Check if no media is playing (all fields show "not provided" or empty)
        if (track_details.get('Title', '') in ['Not Provided', ''] and 
            track_details.get('Artist', '') in ['Not Provided', '']):
            self.track_info_label.set_markup(
                "<span size='large'><b>No media is playing</b></span>\n" +
                "Click play button to start playing"
            )
            self.set_fallback_image()
            # Enable all playback control buttons when device is connected
            for button in [self.play_pause_button, self.shuffle_button, 
                        self.repeat_button]:
                button.set_sensitive(True)
            self.progress_bar.set_value(0)
            self.current_time_label.set_text("0:00")
            self.total_time_label.set_text("0:00")
            return True

        if track_details != self.last_track_details:
            self.last_track_details = track_details
            
            title = html.escape(track_details.get('Title', 'Unknown'))
            artist = html.escape(track_details.get('Artist', 'Unknown'))
            
            track_info = f"<span size='x-large'><b>{title}</b></span>\n{artist}"
            self.track_info_label.set_markup(track_info)

            is_playing = track_details.get("Status", "").lower() == "playing"
            self.play_pause_button_icon.set_from_icon_name(
                "media-playback-pause-symbolic" if is_playing else "media-playback-start-symbolic",
                Gtk.IconSize.LARGE_TOOLBAR
            )

            # Update shuffle and repeat states based on bluetoothctl output
            if "Shuffle: alltracks" in output:
                self.shuffle_mode = True
                self.shuffle_button.get_style_context().add_class('active')
            else:
                self.shuffle_mode = False
                self.shuffle_button.get_style_context().remove_class('active')

            if "Repeat: alltracks" in output:
                self.repeat_mode = "alltracks"
                self.repeat_button.get_style_context().add_class('active')
            elif "Repeat: singletrack" in output:
                self.repeat_mode = "singletrack"
                self.repeat_button_icon.set_from_icon_name("media-playlist-repeat-one-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
                self.repeat_button.get_style_context().add_class('active')
            else:
                self.repeat_mode = "off"
                self.repeat_button_icon.set_from_icon_name("media-playlist-repeat-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
                self.repeat_button.get_style_context().remove_class('active')

            # Only fetch album art if the track has changed
            track_id = f"{title}-{artist}"
            cached_url = self.album_art_cache.get(track_id)
            
            if cached_url:
                response = requests.get(cached_url)
                loader = GdkPixbuf.PixbufLoader()
                loader.write(response.content)
                loader.close()
                pixbuf = loader.get_pixbuf()
                scaled_pixbuf = pixbuf.scale_simple(200, 200, GdkPixbuf.InterpType.BILINEAR)
                self.album_art_image.set_from_pixbuf(scaled_pixbuf)
            elif self.access_token and track_id != self.album_art_cache.last_track:
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

        return True

    def on_play_pause_clicked(self, widget):
        if self.no_player_available:
            self.show_error_dialog("No media player connected. Please connect a device first.")
            return
        current_status = self.last_track_details.get("Status", "").lower()
        if current_status == "playing":
            control_bluetooth("pause")
            self.play_pause_button_icon.set_from_icon_name("media-playback-start-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        else:
            control_bluetooth("play")
            self.play_pause_button_icon.set_from_icon_name("media-playback-pause-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        self.update_track_info()

    def on_next_clicked(self, widget):
        if self.no_player_available:
            self.show_error_dialog("No media player connected. Please connect a device first.")
            return
        control_bluetooth("next")
        self.update_track_info()

    def on_previous_clicked(self, widget):
        if self.no_player_available:
            self.show_error_dialog("No media player connected. Please connect a device first.")
            return
        control_bluetooth("previous")
        self.update_track_info()

    def on_shuffle_clicked(self, widget):
        if self.no_player_available:
            self.show_error_dialog("No media player connected. Please connect a device first.")
            return
        self.shuffle_mode = not self.shuffle_mode
        control_bluetooth("shuffle alltracks" if self.shuffle_mode else "shuffle off")
        if self.shuffle_mode:
            self.shuffle_button.get_style_context().add_class('active')
        else:
            self.shuffle_button.get_style_context().remove_class('active')
        self.update_track_info()

    def on_repeat_clicked(self, widget):
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
        
        self.update_track_info()

def main():
    window = BluetoothControlWindow()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    window.queue_draw()
    Gtk.main()

if __name__ == "__main__":
    main()