GUI implementation
-----

.. contents:: Contents
    :depth: 3
    :local:

MVP design pattern
.....
EVA uses the MVP/MVC design pattern to separate GUI code and logi
c code. This helps write "cleaner" code and allows us
to pick out the logic bits and test them independently without having to deal with the GUI. The implementation of this
is continuously being improved.

The basic principle is that any complex widget or window should be made up of a view, presenter and a model.
There are many tutorials on how this is done, such as this_ one.

.. _this: https://developer.mantidproject.org/MVPDesign.html

The model, view, and presenter are linked together by a 4th object, usually named ``xxx_widget.py``, and this widget
is what you would then import into your code to use your custom widget/window as if it was any other PyQt widget.

There are a few reusable widgets available which provide methods that are commonly used to avoid code duplication, such as
BaseView, BaseTableWidget and PlotWidget. If you see a method being used in a widget that you cannot find within the class definition,
it was likely inherited from one of these base widgets.

Qt Designer
.....
If you are designing a new interface or widget, it is strongly recommended that you use Qt Designer
(not to be confused with Qt Creator!) to do this, rather than writing the GUI code yourself.

Here_ is a tutorial on how to install and use Qt Designer (because for some reason there is no standalone installer),
as well as how generate code from the .ui file.

.. _Here: https://www.youtube.com/watch?v=FVpho_UiDAY

To make it work with PyQt6, install ``pyqt6-tools`` instead, and you should be able to find the program installed
under ``[name of virtual environment]/Lib/site-packages/qt6_applications/Qt/bin/designer.exe``. When generating gui files,
you will have to run ``pyuic6.exe`` rather than ``pyuic5.exe``.

I recommend just designing the GUI in qt designer and setting up all button connections in the presenter.
Once you have generated your gui file, add it to src/EVA/gui/ and generate the python gui file. From this,
you can use your GUI file in the code by having the view inherit from the generated gui file.

There are a few shortcomings with Qt Designer which require some workarounds. If you want to use a custom widget in
Qt Designer such as a PlotWidget or a BaseTableWidget, you can work around this by "promoting widgets".
Here is a relevant guide_.

.. _guide: https://www.youtube.com/watch?v=VFV1nljhfJ8.

As an example, if you want to promote your QTableWidget to BaseTableWidget, in the widget promotion menu
you would enter "BaseTableWidget" under class name and "EVA.widgets.base.base_table" under header file.
This will then automatically include the custom widget when generating the gui file.

