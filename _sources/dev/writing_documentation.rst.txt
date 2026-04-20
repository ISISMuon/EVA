Writing documentation
===========================

Overview
.............
A large portion of this documentation is actually generated from the EVA source code itself! These pages are generated using `Sphinx`_.

.. _Sphinx: https://www.sphinx-doc.org/en/master/

The source code for these webpages is located in the doc/ folder of the repository.
The pages are written in reStructured Text (.rst files), which can be built to HTML by Sphinx using the command

.. code-block::

    sphinx-build doc <destination_folder>

You can then go to the destination folder and open index.html with a web browser to see the documentation pages.

The settings for building the documentation are set in the docs/conf.py file. A couple of extensions are used to make the
documentation more automated.

Docstrings
....................
Docstrings are a way of embedding documentation directly into the code and makes it easier for others to see what the code is doing.
It is best practice to write a docstring for all classes and functions that you write. There are a few different docstring styles,
such as NumPy, Google, etc. EVA uses the Google format. Some IDEs like PyCharm can automatically generate docstring templates - you can set up the
default format to Google style. It is also recommended to type hint all code!

The sphinx autodoc extension is used to automatically pull information from the docstrings in the code to generate webpages with documentation for
methods and classes, as seen in the Code Documentation section. This is why consistency in docstring format is important - If doscrings are
formatted incorrectly this will not work.

To add a section with code documentation to a page in reStructured Text, use the automodule keyword in the .rst file. Example:

.. code-block::

    .. automodule:: EVA.core.physics.normalisation
    :members:

There is also an auto typing extension which automatically pulls the types from the type hinting so you don't need to write them in the
doctrings.

Updating this website
.....................................
There is a github action (in the .github/workflows folder) set up which automatically re-builds the documentation and
updates the webpage every time the main branch updates (for example when a pull request into main is completed).
Therefore you should only build the documentation locally to test if your .rst files are formatted correctly - no need to
add any HTML to the repository.

There seems to be some bug with some of the auto-documentation not working properly - seems to be working OK when building locally
but when built using the github actions some of the modules cannot be found or fail to build
(error logs can be found under the actions tab of the repository).


