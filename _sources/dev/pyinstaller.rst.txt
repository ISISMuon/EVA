Building executables with pyinstaller
------------------------------------------
EVA uses pyinstaller_ to freeze the python project into an executable which contains all requirements and
dependencies needed to run. (This is why having a c++ compiler installed is needed). The ``EVA.spec`` file specifies all the settings
and parameters we want for the executable. Pyinstaller has two different modes it can use when creating the
executable, either a single executable (one-file mode) or a folder containing the executable and some dependencies
(one-folder mode). This project uses the one-folder mode, as it is easier to debug.

To build the executable, you just need to run

.. code-block::

    pyinstaller EVA.spec

which will generate the executable under ``dist/main/EVA.exe``.

.. _pyinstaller: https://pyinstaller.org/en/stable/

Pyinstaller will produce an executable type depending on the platform the pyinstaller command is ran on. Building with
pyinstaller has only been tested for Windows, but it should work for MacOS and Linux too.


Automatically building executables
.....................................

There is a github action set up to automatically run pyinstaller every time a new pull request is made (under .github/workflows).
To get the latest executable after a pull request, you can download it from the actions tab.