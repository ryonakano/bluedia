project('io.github.codes-by-chetan.bluedia', 'c')

# Check if required dependencies are available
cairo_dep = dependency('cairo', required: true)
gobject_dep = dependency('gobject-2.0', required: true)


# Find Python3 and venv module
python = find_program('python3', required: true)
venv_module = run_command(python, '-c', 'import venv', check: false)
if venv_module.returncode() != 0
    error('Python venv module not found. Please install python3-venv')
endif

# Create virtual environment in build directory
message('Creating virtual environment...')
venv_dir = meson.current_build_dir() / 'venv'
venv_result = run_command(python, '-m', 'venv', venv_dir, check: false)
if venv_result.returncode() != 0
    error('Failed to create virtual environment: ' + venv_result.stderr().strip())
endif

# Get venv paths
venv_python = venv_dir / 'bin' / 'python'
venv_pip = venv_dir / 'bin' / 'pip'

# Upgrade pip and install wheel
message('Upgrading pip and installing wheel...')
run_command(venv_python, '-m', 'pip', 'install', '--upgrade', 'pip', 'wheel', check: true)

# Install PyInstaller and dependencies
message('Installing PyInstaller and dependencies...')
run_command(venv_pip, 'install', 'pyinstaller', 'PyGObject', 'requests', check: true)

# Create spec file content
spec_content = '''# -*- mode: python -*-
import sys
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = collect_submodules('gi') + ['requests']

a = Analysis(['@0@'],
             binaries=[],
             datas=[('@1@', '.')],
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='bluedia',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False)
'''.format(meson.source_root() / 'src' / 'bluedia.py',
           meson.source_root() / 'data' / 'icons' / 'bluedia.png')

# Write spec file in build directory
spec_file = meson.current_build_dir() / 'bluedia.spec'
run_command('sh', '-c', 'echo "' + spec_content + '" > ' + spec_file, check: true)

# Build executable using PyInstaller
message('Building executable with PyInstaller...')
pyinstaller_result = run_command(venv_python, '-m', 'PyInstaller', '--clean', 
                                 '--workpath=' + meson.current_build_dir() / 'build',
                                 '--distpath=' + meson.current_build_dir() / 'dist',
                                 spec_file, check: false)
if pyinstaller_result.returncode() != 0
    error('PyInstaller failed: ' + pyinstaller_result.stderr().strip())
endif

# Define project name and installation directories
name = 'bluedia'
prefix = get_option('prefix')
bindir = join_paths(prefix, get_option('bindir'))
datadir = join_paths(prefix, get_option('datadir'))
icondir = join_paths(datadir, 'icons', 'hicolor')

# Install the executable from build/dist directory
install_data(
    meson.current_build_dir() / 'dist' / 'bluedia',
    install_dir: bindir,
    install_mode: 'rwxr-xr-x'
)

# Install the desktop file
install_data(
    meson.source_root() / 'data' / 'bluedia.desktop',
    install_dir: join_paths(datadir, 'applications')
)

# Install icon
install_data(
    meson.source_root() / 'data' / 'icons' / 'bluedia.png',
    install_dir: join_paths(get_option('prefix'), get_option('datadir'), 'icons', 'hicolor', '128x128', 'apps')
)

# Install the appdata file
install_data(
    meson.source_root() / 'data' / 'bluedia.xml',
    install_dir: join_paths(datadir, 'metainfo')
)