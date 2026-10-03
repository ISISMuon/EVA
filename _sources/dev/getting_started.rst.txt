Getting started
====================

.. contents:: Contents
    :depth: 3
    :local:

Setting up your environment
------------------------------
EVA requires Python 3.12 or newer. If you do not have a preferred text editor/IDE I recommend using PyCharm or VSCode
as they both have many integrated tools that make the development process much easier and faster.

Once you have the correct version of Python installed, you'll want to make sure you have a C++ compiler installed.
If developing on Windows, you can follow `this guide`_ to install it.
If developing on Linux, you just need to install gcc (if not already installed), and if you're working on MacOs you can install Xcode.

Next, you'll want to set up a `virtual environment`_. *Tip: some IDEs can do this for you*. Once you've done that you can install all requirements using pip:

.. _this guide: https://github.com/bycloudai/InstallVSBuildToolsWindows
.. _virtual environment: https://docs.python.org/3/library/venv.html

.. code-block::

    pip install -r "requirements.txt"


Lastly, EVA needs to be installed before it can run. For developing purposes, you can install an editable build using

.. code-block::

    pip install . -e

which will update the installed EVA package every time you edit the code, meaning you only have to run this
once when setting up the environment and forget about it.
