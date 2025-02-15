project('oscillate',
    version: '1.5-INDEV',
    meson_version: '>= 0.59.0',
    default_options: [
    'warning_level=2',
    'werror=false',
  ],
)

python = import('python')
py_installation = python.find_installation('python3', required: true, modules: ['gi'])

gnome = import('gnome')

compiled_schemas = gnome.compile_schemas(
  build_by_default: true,
  depend_files: 'data/glib-2.0/schemas/com.example.Oscillate.gschema.xml'
)

install_subdir('src', install_dir: get_option('prefix'))

install_data(
  'data/glib-2.0/schemas/com.example.Oscillate.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

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
    install_dir: py_installation.get_install_dir() / 'oscillate'
)

install_data('com.example.Oscillate.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

# Install Python package
python_sources = [
    'src/oscillate/__init__.py',
    'src/oscillate/main.py',
    'src/oscillate/window.py',
    'src/oscillate/player.py',
    'src/oscillate/preferences.py',
]

py_installation.install_sources(
  python_sources,
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