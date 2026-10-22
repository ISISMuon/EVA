Code overview
===============
EVA is based on PyQt6, which is a Python binding of Qt which is a C++ library for creating cross-platform GUIs.
If you are new to PyQt I recommend these_ tutorials.

.. _these: https://www.pythonguis.com/pyqt6-tutorial/

.. contents:: Contents
    :depth: 3
    :local:

File structure
-----------------

This project uses a `src layout`_, meaning all source code will be located in the ``src`` folder, keeping other things like
project configurations and unit tests outside of the source directory.

Inside the ``src`` folder there are two folders:

.. _src layout: https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html

* ``EVA`` which contains all the EVA source code
* ``srim`` which contains a modified version of pysrim - see `pysrim implementation`_ for why

Within the EVA folder we have:

* ``core/`` contains most of the fundamental non-gui things such as fitting functions, database loading, data loading, config files etc.
* ``databases/`` contains JSON databases for muonic xray transitions, gamma transitions and electronic xrays.
* ``gui/`` contains all of the GUI code and "features"
* ``resources/`` contains images, icons, manual etc.
* ``util/`` contains a few "utility" functions

Code entry point
------------------
The main code entry point is ``src/EVA/main.py``. main.py creates an instance of the QApplication and runs it. This is the
main "event loop" which keeps the program running until user closes the application.

Custom app class
-------------------
EVA uses a custom subclass of QApplication which is located under ``src/EVA/core/app.py``. All global information,
such as user configurations and databases, are stored within this class, and can be accessed anywhere. Take care not to
clutter this too much - only store things in the app if the need to be globally accessible. The App class is a singleton
instance, meaning there is only ever one App instance at once, and all references to the app will point to the same object.

The App instance can be quickly accessed anywhere by calling ``QApplication.instance()`` or using the wrapper
function ``get_app()`` from app.py. The App class also has a wrapper function ``get_config()`` which returns the
current configuration of the app.

Main window
---------------
``src/EVA/gui/windows/main/main_window.py`` is the EVA "main window" which is shown on start up. This window is responsible
for launching all other windows. It is made up of a view, model, and presenter - see the GUI guide for more on this.
All EVA features which do not require experiment data to run can be accessed from this window. When a user loads a run number,
the main window will open up a workspace window.

Workspaces
---------------
Every time a run is loaded, a new workspace is loaded. In the workspace, the user can use elemental analysis and peak fitting tools.
All other tools are also available here, most of which will open as tabs to avoid having many windows opening.

Config files
-------------------
EVA uses .json files to save configurations. The config class, located under ``src/EVA/core/settings/config.py``, handles
everything related to configurations. Default settings are stored in ``src/EVA/core/settings/defaults.json``
The first time EVA is ran, a copy of defaults.json is created under ``src/EVA/core/settings/config.json``. When settings are saved
by the user, config.json is updated.

pysrim implementation
------------------------
Previous versions of EVA (<2.4.1) contained a vendored (modified copy) version of pysrim (under src/srim) due to a bug in the version of pysrim available on pypi. The fix was to change srim/core/elementdb.py:

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

However this fix has been implemented in the main repository, just not updated on pypi,
so this has since been fixed by installing a clone of the repo:

.. code-block::

    pip install git+https://gitlab.com/costrouc/pysrim.git@master

Note that the pysrim repository uses git LFS which fails_ to clone and install when installing using Git versions <=v2.45.1 (`git archive`_)

.. _fails: https://github.com/git-lfs/git-lfs/issues/5749

.. _git archive: https://lore.kernel.org/git/xmqqr0dheuw5.fsf@gitster.g/T/#u