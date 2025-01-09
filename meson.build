# project name, programming language, and required meson version
project('io.github.codes-by-chetan.yourrepositoryname',
    'vala', 'c',
    meson_version: '>= 0.56.0'
)

# Create a new executable, list the files we want to compile, list the dependencies we need, and install
executable(
    meson.project_name(),
    'src' / 'Application.vala',
    dependencies: [
        dependency('gtk4')
    ],
    install: true
)

# Install our .desktop file so the Applications Menu will see it
install_data(
    'data' / 'hello-again.desktop',
    install_dir: get_option('datadir') / 'applications',
    rename: meson.project_name() + '.desktop'
)

# Install our .metainfo.xml file so AppCenter will see it
install_data(
    'data' / 'hello-again.metainfo.xml',
    install_dir: get_option('datadir') / 'metainfo',
    rename: meson.project_name() + '.metainfo.xml'
)