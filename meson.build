project('com.codes-by-chetan.bluetooth-media-controller',
        version: '1.0.0',
        meson_version: '>= 0.50.0'
)

python = import('python')
python_installation = python.find_installation('python3',
    required: true,
    modules: [
        'gi',
        'requests'
    ]
)

dependency('gtk+-3.0', version: '>= 3.0')
dependency('glib-2.0')
dependency('gobject-2.0')

# Dependencies from build-app.js
run_command('pip3', 'install', 'PyGObject', 'requests', check: true)

# Install Python script
install_data(
    'src/bluetooth-media-controller.py',
    install_dir: get_option('bindir'),
    rename: 'com.codes-by-chetan.bluetooth-media-controller'
)

# Install desktop file
install_data(
    'data/com.codes-by-chetan.bluetooth-media-controller.desktop',
    install_dir: join_paths(get_option('datadir'), 'applications')
)

# Install AppStream metadata
install_data(
    'data/com.codes-by-chetan.bluetooth-media-controller.appdata.xml',
    install_dir: join_paths(get_option('datadir'), 'metainfo')
)

# Install icon
install_data(
    'data/icons/com.codes-by-chetan.bluetooth-media-controller.png',
    install_dir: join_paths(get_option('datadir'), 'icons', 'hicolor', '128x128', 'apps')
)

# Install license
install_data(
    'LICENSE',
    install_dir: join_paths(get_option('datadir'), 'doc', meson.project_name())
)