Web Application Interface
=========================

Overview
--------

The code is hooked up to a simple web application at https://hursts.org.uk/aims.

The control bar on the left gives you radio buttons to select between three
output formats: eFJ; iCalendar; and CSV. Selecting iCalendar output additionally
gives you the option to include all day events.

Once the output format is selected, upload your roster, either with the "Load
Roster" button or by drag and dropping it. The right hand side will then show
the converted roster in a simple text editor.

Once you are happy with the output, either download it with the "Save" button or
copy it to the clipboard with the "Copy All" button. You can also select parts
of the output and copy it to the clipboard by right clicking.

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
