Web Application Interface
=========================

Overview
--------

The web application is available at https://hursts.org.uk/aims.

This application converts data exported from easyJet’s AIMS servers into one of
the three output formats discussed in the `Output Formats`_ section below. If
you are not an easyJet pilot you *may* also be able to make use of this if your
airline uses the same version of AIMS as easyJet.

The application accepts either a vertical AIMS “Crew Schedule” or an AIMS “Pilot
LogBook report“ as input. These are available from the AIMS web interface at
https://ezy-crew.aims.aero.

The “Crew Schedule" should generally be preferred since it includes accurate
duty times, full crew, and non-flying duties. It does, unfortunately, lack
details of the aircraft registration, including only the aircraft type, and data
can only be downloaded in chunks of up to 31 days. To download it, go to ``Crew
Schedule | My Schedule``, select the required period, then click the ``Print``
button. The viewer that appears has an ``Export To`` button on its taskbar.
Click this and select ``HTML``.

The “Pilot Logbook report” can be downloaded in chunks of up to two years, and
includes the aircraft registrations. Since it doesn't include actual report and
off duty times, these are approximated based on standard report and debrief
times when using this input. To download it, go to ``Reports | Pilot LogBook
report``, set the required period and click ``Go``. Again, the viewer has an
``Export To`` button, from which you should select ``HTML``.

The control bar on the left gives you radio buttons to select between three
output formats: ``eFJ``; ``iCalendar``; or ``CSV``. Selecting ``iCalendar``
output additionally gives you the option to include all day events.

Once the output format is selected, upload your report, either with the "Load
Report" button or by drag and dropping it. The right hand side will then show
the converted roster in a simple text editor.

Once you are happy with the output, either download it with the ``Save`` button or
copy it to the clipboard with the ``Copy All`` button. You can also select parts
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
