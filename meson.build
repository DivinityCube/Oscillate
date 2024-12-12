project('oscillate',
    version: '0.1.0',
    meson_version: '>= 0.59.0'
)

python = import('python')
python_installation = python.find_installation('python3')
gnome = import('gnome')

# Dependencies
dependency('glib-2.0')
dependency('gtk4')
dependency('libadwaita-1')

# GResource
resources = gnome.compile_resources(
    'com.example.Oscillate',
    'src/com.example.Oscillate.gresource.xml',
    source_dir: 'src',
    gresource_bundle: true,
    install: true,
    install_dir: python_installation.get_install_dir() / 'oscillate'
)

# Install GSchema
install_data(
    'data/com.example.Oscillate.gschema.xml',
    install_dir: get_option('datadir') / 'glib-2.0' / 'schemas'
)

# Install Python package
python_sources = [
    'src/oscillate/__init__.py',
    'src/oscillate/main.py',
    'src/oscillate/window.py',
    'src/oscillate/player.py',
    'src/oscillate/preferences.py',
]

python_installation.install_sources(
    python_sources,
    pure: true,
    subdir: 'oscillate'
)

# Install UI file
install_data(
    'src/oscillate/window.ui',
    install_dir: python_installation.get_install_dir() / 'oscillate'
)

# Configure and install the executable script
conf = configuration_data()
conf.set('PYTHON', python_installation.full_path())
conf.set('prefix', get_option('prefix'))
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('projectname', meson.project_name())

configure_file(
    input: 'bin/oscillate.in',
    output: 'oscillate',
    configuration: conf,
    install: true,
    install_dir: get_option('bindir'),
    install_mode: 'rwxr-xr-x'
)

# Post-install script
meson.add_install_script('build-aux/meson/postinstall.py')