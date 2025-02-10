project('bluedia',
        version: '1.0.0',
        meson_version: '>= 0.50.0'
)

# Python installation
python = import('python')
py_installation = python.find_installation('python3')
if not py_installation.found()
    error('No valid python3 installation found')
endif

# Dependencies
dependency('gtk+-3.0', version: '>= 3.0')

# Installation paths
prefix = get_option('prefix')
bindir = join_paths(prefix, get_option('bindir'))
datadir = join_paths(prefix, get_option('datadir'))
icondir = join_paths(datadir, 'icons', 'hicolor')
applicationsdir = join_paths(datadir, 'applications')

# Install Python script
install_data('src/bluedia.py',
             install_dir: bindir,
             rename: 'bluedia',
             install_mode: 'rwxr-xr-x'
)
configure_file(
    input: 'src/bluedia.py',
    output: 'bluedia',
    copy: true,
    install: true,
    install_dir: bindir,
    install_mode: 'rwxr-xr-x'
)

# Install desktop file
install_data('data/bluedia.desktop',
             install_dir: applicationsdir
)

# Install icons
install_data('data/icons/bluedia.png',
             install_dir: join_paths(icondir, '256x256', 'apps')
)

# Install app metadata
install_data('data/bluedia.xml',
             install_dir: join_paths(datadir, 'metainfo')
)
