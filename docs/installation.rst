Installation
============

Web Application
---------------

The code has been connected to a web application at https://hursts.org.uk/aims.
This requires no installation, just a reasonably modern browser.


Local installation
------------------

Local installation provides greater flexibility and a slicker experience, as
well as the ability to use the code as a library. It also removes reliance on
the continued provision of the web application.

A Python interpreter with version 3.11 or newer is required.

Linux users will almost certainly already have this pre-installed. Some
distributions package tkinter separately, so this may need to be installed if
you wish to use the graphical interface.

Windows users can find the Python interpreter in the Microsoft Store by
searching for "Python" — ensure it is the app published by the Python Software
Foundation that you are installing.

Mac users should visit https://www.python.org to download an installer.


Installation with pip
^^^^^^^^^^^^^^^^^^^^^

If you are familiar with pip, aims-convert is available from PyPi. Install with
your favourite variation of::

   pip install aims-convert

This also installs the entry point for the command line interface, ``aims`` and
an entry point for a Tk based graphical user interface, ``aimsgui``. Note pip's
warning to adjust your PATH environmental variable if installing on Windows with
the Microsoft Store version of the Python interpreter.

Single file install
^^^^^^^^^^^^^^^^^^^

The graphical interface can be installed by downloading from
https://hursts.org.uk/shiv/aimsgui.pyw and copying to a location of your
choosing. If you need to deal with rosters downloaded before easyJet’s July
2024 AIMS update, you can use version 1.2 which is available to download at
https://hursts.org.uk/shiv/aimsgui-1.2.pyw.

Windows users can just double click on this to run it. Linux and Mac users need
to set the executable permission on the file and can then run it as they would
any other script.

Uninstalling just requires deleting the file. Running the program creates a
settings file named ``.aimsgui`` and a cache directory named ``.shiv`` that can
be deleted at any time. These can be found in your home/user directory.
