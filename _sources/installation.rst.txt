Installation Guide
====
If you are on a Windows system, you can just download the executable from Github. If you are using Linux
or MacOS you will have to install EVA using pip.

Note that you may need to have C++ build tools installed in order to install from source.

Installing with pip
----
EVA requires Python 3.12 or newer to run.

Download the project from Github and unzip to a destination of your choice.
It is strongly recommended you create a virtual environment before installing.

Once in your virtual environment, install all requirements using:

.. code-block::

    pip install -r "requirements.txt"


After ``pip`` has installed all requirements, ensure you are in the project root directory and
install EVA by running

.. code-block::

    pip install .

Once this is done you can start EVA by running ``main.py`` in src/EVA.






