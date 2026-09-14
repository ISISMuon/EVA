Unit testing
===============

EVA uses pytest and pytest-qt for unit testing. It is best practice to write a unit test for every new function / feature
that is added to the code. Currently, there are quite a few features in EVA which do not yet have unit tests and require manual testing.

The unit tests are located in the tests/ folder. Tests should be separate from the source code so that they can test the
program externally. The tests are separated into GUI test and system tests.

To run the tests, run the command

.. code-block::

    pytest

To run a specific folder or test simply specify the path:

.. code-block::

    pytest tests/gui

To get console outputs (from print statements) use the -s flag:

.. code-block::

    pytest test/gui/test_manual.py -s

Pytest introduces the concept of fixtures, which are very useful for writing clean and reusable tests. You can read
more about `fixtures here`_.

.. _`fixtures here`: https://docs.pytest.org/en/6.2.x/fixture.html


System tests
................
System tests test the logic parts of the code. This includes database loading, mathematical functions and features in widget models.

GUI tests
...........
GUI tests can be a little more involved as they tend to require the qtbot fixture to run properly.

Test config
..............
conftest.py sets up the test environment before any tests are run. It overrides the app-cls fixtures to ensure that pytest
creates an instance of the custom QApplication class that EVA uses, and ensures that the app uses the appropriate test conditions.

Test teardown
................
If a test is altering the state of the program, it is important to ensure that any changes are reset before the test is finished,
otherwise the outcome of tests could depend on the order they are run in! The best way to do this is using fixtures and the yield keyword.
Read more about `teardown here`_.

.. _`teardown here`: https://docs.pytest.org/en/6.2.x/fixture.html#safe-teardowns

Automatic testing with Github actions
........................................
There is a github action set up which will run pytest every time a new pull request is made (in .github/workflows). This allows for automatically
checking if any new changes are breaking. This is why it is important to add more unit tests to EVA - the more tests,
the less likely it is that breaking changes / new bugs are introduced with updates.
