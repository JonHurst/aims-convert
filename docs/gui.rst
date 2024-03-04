Graphical User Interface
========================

Overview
--------

This is a simple, cross platform Tk based GUI front end. It relies on Python's
tkinter module, which is normally installed by default with the Python
interpreter. Some Linux distributions don't install this module by default, so
it may need to be installed with your package manager if you wish to use the
GUI. For example, Debian and Ubuntu require::

  $ sudo apt install python3-tk

The control bar on the left has radio buttons to select the output type. If you
select "Roster (.ics)", you additionally have the option to include all day
events such as days off.

Use the "Load Roster" button to choose the roster to convert. The output will
appear in a simple text editor on the right.

Once you are happy with the output, either save it with the "Save" button or
copy it to the system clipboard with "Copy All". If text is selected in the text
editor, this button changes to "Copy Selected" to allow parts of the output to
be copied.

Output Formats
--------------

electronic Flight Journal (eFJ)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a text file based scheme for efficiently managing your flying logbook.
Details of the scheme and tools for working with it can be found at
https://hursts.org.uk/efjtkdocs.

iCalendar
^^^^^^^^^

`iCalendar files <https://icalendar.org>`_ are the standard way to transfer
calendar data. This output can be imported into Google Calendar, Outlook etc.

Each entry has an identifier built from the start time of the duty and a list of
airports involved or, for all day events, the date and description of the duty.
This means that re-uploading an iCalendar file should update your calendar
correctly; there is, however, no mechanism for removing entries that have been
deleted from your roster since the last upload, so this will have to be done
manually.

CSV
^^^

A Comma Separated Values (CSV) file with Excel conventions. This can be used as
a basis for getting data in to a spreadsheet based logbook — all mainstream
spreadsheets are capable of importing these CSV files.
