# Bluetooth Media Controller

A Python tool to control Bluetooth audio devices and display the currently playing track with playback controls. It uses `bluetoothctl` to manage Bluetooth connections and interacts with the audio devices.

## Features

- Connect to Bluetooth audio devices.
- Display the currently playing track on connected Bluetooth audio devices.
- Provide basic playback controls: Play, Pause, Next, and Previous.
- Command-line interface for interaction.

## Installation

## Prerequisites

Before using this tool, ensure that you have Python 3.6+ installed and `bluetoothctl` configured on your system.

### Clone the Repository

Clone the repository to your local machine:

```bash
    git clone https://github.com/yourusername/bluetooth_media_controller.git
    cd bluetooth_media_controller
```


### Install Dependencies
Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```
Alternatively, you can directly install the package by running:
```bash
python setup.py install
```

### Dependencies
- `gi`: For interacting with Bluetooth devices.
- `requests`: For making HTTP requests (if needed for future features).
- `base64`, `html`: For encoding/decoding media data.


### Usage
Once the tool is installed, you can run it using Python to control Bluetooth devices.

Example Command
```bash
python bluetooth_media_controller.py
```

This will start the application and display the currently playing track and provide playback controls.


### Available Commands
- Play: Starts playing the current track.
- Pause: Pauses the current track.
- Next: Skips to the next track.
- Previous: Goes back to the previous track.
- You can customize these commands and extend them as needed.

## Contributing
If you'd like to contribute to the development of this project, please follow these steps:

- Fork the repository.
- Create a new branch (git checkout -b feature-name).
- Make your changes.
- Commit your changes (git commit -am 'Add new feature').
- Push to the branch (git push origin feature-name).
- Create a new Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
Thanks to the developers of bluetoothctl and gi for providing the tools to interact with Bluetooth devices.

