# Bluetooth Media Controller

A Python tool to control Bluetooth audio devices and display the currently playing track with playback controls. It uses `bluetoothctl` to manage Bluetooth connections and interacts with the audio devices.

## Features

- Connect to Bluetooth audio devices
- Display the currently playing track on connected Bluetooth audio devices
- Provide basic playback controls: Play, Pause, Next, and Previous
- Command-line interface for interaction

## Prerequisites

Before installing and using this tool, ensure that you have the following prerequisites:

- Python 3.6+
- GTK 3
- BlueZ v5.70 or higher
- Meson (0.50 or newer)
- Ninja

## Installation

### Clone the Repository

Clone the repository to your local machine:

```bash
git clone https://github.com/yourusername/bluetooth_media_controller.git
cd bluetooth_media_controller
```

### Build and Install

1. Set up the build directory:

```bash
meson build
```

2. Compile the project:

```bash
ninja -C build
```

3. Install the application:

```bash
sudo ninja -C build install
```

## Post-Installation Steps

After installation, you can run the Bluetooth Media Controller using the following command:

```bash
bluetooth-media-controller
```

If the command is not found, you may need to log out and log back in or restart your system for the PATH to update.

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

If you'd like to contribute to the development of this project, please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature-name`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature-name`)
6. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Thanks to the developers of BlueZ, GTK, and the Python GObject Introspection library for providing the tools to interact with Bluetooth devices and create the user interface.