# Bluedia - Bluetooth Media Controller

Bluedia is a Python-based tool that allows you to control Bluetooth audio playback from your Linux desktop. It provides a GTK interface to interact with Bluetooth audio devices, display track details, and manage playback.

## Features

- Play, pause, skip, and go back to the previous track
- Display currently playing track details (title, artist, album)
- Fetch and display album art from Spotify
- Show playback progress with a progress bar
- Supports shuffle and repeat modes
- Manual refresh button to update track details
- Debug logging for troubleshooting

## Prerequisites

Ensure you have the following dependencies installed before proceeding:

- Python 3.6+
- GTK 3
- PyGObject
- BlueZ (v5.70 or higher)
- Meson (0.50 or newer)
- Ninja
- `requests` Python library

To install missing dependencies on Ubuntu, run:

```bash
sudo apt update && sudo apt install python3-gi gir1.2-gtk-3.0 python3-pip python3-venv meson ninja-build
pip3 install requests
```

## Installation

### Clone the Repository

```bash
git clone https://github.com/codes-by-chetan/bluedia.git
cd bluedia
```

### Build and Install

1. Set up the build directory:

   ```bash
   meson setup build
   ```

2. Compile the project:

   ```bash
   ninja -C build
   ```

3. Install the application:

   ```bash
   sudo ninja -C build install
   ```

## Running the Application

After installation, launch Bluedia with:

```bash
bluedia
```

If the command is not found, try logging out and back in or restarting your system to refresh the environment.

## Usage Guide

### Connecting to a Bluetooth Device
1. Open your device's Bluetooth settings and connect to your computer.
2. Ensure media playback control is enabled for the connected device.
3. Open **Bluedia** to start controlling playback.

### Controls
- **Play/Pause**: Toggle playback.
- **Next**: Skip to the next track.
- **Previous**: Go back to the previous track.
- **Shuffle**: Toggle shuffle mode.
- **Repeat**: Cycle through repeat modes (off, all, single).
- **Refresh**: Manually refresh track details.

### Debugging Issues
If Bluedia does not work correctly, try the following:
- Ensure your **BlueZ** version is at least **5.70** (`bluetoothctl --version`).
- Run Bluedia in a terminal to view debug logs:
  
  ```bash
  bluedia
  ```
- If the app does not open, check for missing dependencies and reinstall them.

## Usage

As a linux user, you know that if you connect your phone to the computer via bluetooth, it starts sending audio to your computer and you can play media of your phone using your computer's speakers. But you can not control the media playback from your computer. This application is designed to solve this problem.

Once the tool is installed and running, you can use it to control Bluetooth devices.
- 1) Connect to a Bluetooth device. To connect go to your device settings >> bluetooth.
- 2) Once connected, you can use the tool to control the device. You can play, pause, stop, and skip tracks.
- 3) You can also use the tool to change the play modes of the device.
- 4) If the tool is not working then you should try updating the bluez to the latest version in your computer. Make sure you have the bluez v5.70 or higher. You can do visit for more details : [bluez update](https://askubuntu.com/questions/612295/how-to-upgrade-to-the-latest-bluez-version-on-ubuntu-12-04-lts)

### Available Commands

- Play: Starts playing the current track
- Pause: Pauses the current track
- Next: Skips to the next track
- Previous: Goes back to the previous track

You can customize these commands and extend them as needed.

## Contributing

If you'd like to contribute to Bluedia, follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-name`).
3. Make your changes and commit them.
4. Push to your branch (`git push origin feature-name`).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

Thanks to the developers of BlueZ, GTK, and PyGObject for providing the tools necessary to build this project.
