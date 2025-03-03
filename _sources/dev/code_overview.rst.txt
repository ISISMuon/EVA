Code overview
=====
EVA is based on PyQt6, which is a Python binding of Qt which is a C++ library for creating cross-platform GUIs.
If you are new to PyQt I recommend going through one of the many PyQt6 tutorials out there.

.. contents:: Contents
    :depth: 3
    :local:

File structure
-----

This project uses a `src layout`_, meaning all source code will be located in the ``src`` folder, keeping other things like
project configurations and unit tests outside of the source directory.

Inside the ``src`` folder there are two folders:

.. _src layout: https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html

* ``EVA`` which contains all the EVA source code
* ``srim`` which contains a modified version of pysrim - see `pysrim implementation`_ for why

Within the EVA folder we have:

* ``core/`` contains most of the fundamental non-gui things such as fitting functions, database loading, data loading, config files etc.
* ``databases/`` contains JSON databases for muonic xray transitions, gamma transitions and electronic xrays.
* ``gui/`` contains all Qt Designer .ui files and generated python files for the GUI
* ``resources/`` contains images, icons, manual etc.
* ``util/`` contains a few "utility" functions
* ``widgets/`` contains all custom widgets for EVA such as custom tables, plotting widgets, as well view "templates"
* ``windows/`` contains all the standalone windows, including the ``main_window.py`.

Code entry point
-----
The main code entry point is ``src/EVA/main.py``, which creates an instance of the QApplication and runs it. This is the
main "event loop" which keeps the program running until user closes the application.

Custom app class
-----
EVA uses a custom subclass of QApplication which is located under ``src/EVA/core/app.py``. All global information,
such as user configurations and databases, are stored within this class, and can be accessed anywhere. Take care not to
clutter this too much - only store things in the app if the need to be globally accessible. The App class is a singleton
instance, meaning there is only ever one App instance at once.

The App instance can be quickly accessed anywhere by calling ``QApplication.instance()`` or using the wrapper
function ``get_app()`` from app.py. The App class also has a wrapper function ``get_config()`` which returns the current config.

Main window
-----
``src/EVA/windows/main/main_window.py`` is the EVA "main window" which is shown on start up. This window is responsible
for launching all other windows. It is made up of a view, model, and presenter - see the GUI guide for more on this.
When a user loads data, the loaded data will be stored in this window and passed around whenever needed.

Config files
-----
EVA uses the configparser library to manage configurations, which is a part of the Python standard library as of version 3.12.
The configurations are stored in .ini files. The config class, located under ``src/EVA/core/settings/config.py``, handles
everything related to configurations.

pysrim implementation
-----
Inside the src directory you'll find a modified version of pysrim, which is one of the dependencies for EVA.
The src directory also contains a modified version of pysrim. Due to an update in PyYAML, the following modification
has to be made in the pysrim/core/elementdb.py file (as of 28/10/24) in order for it to work properly.

From

.. code-block::
    python

    def create_elementdb():
    dbpath = os.path.join(srim.__path__[0], 'data', 'elements.yaml')
    return yaml.load(open(dbpath, "r"))


to

.. code-block::
    python

    def create_elementdb():
    dbpath = os.path.join(srim.__path__[0], 'data', 'elements.yaml')
    return yaml.load(open(dbpath, "r"), Loader=yaml.FullLoader)


This modification has been made to a copy of pysrim located under src/, but the copy can be removed in the future if
the error is patched in the main repository.





