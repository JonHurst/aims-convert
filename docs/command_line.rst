Command Line Interface
======================

The following assumes that aims-convert has been installed via pip, pipx etc.
and that this has added the ``aims`` entry point to somewhere that is included
in your PATH environmental variable.

The script is written as filter, i.e. it takes input from STDIN, writes to
STDOUT and sends any error information to STDERR. Replace ``aims_roster`` with
the file path of your downloaded roster.

eFJ output
----------

::

   $ aims efj < aims_roster

Writes an `electronic Flight Journal
<https://hursts.org.uk/efjdocs/format.html#overview>`_ to STDOUT. Regulatory
night flying calculations are included. For easyJet pilots, airframe lookup is
carried out — this may fail for very recent flights, in which case the airframe
will be listed as ``?-????:????`` and will need to be updated manually.

iCalendar output
----------------

::

   $ aims ical < aims_roster

Writes `an iCalendar file <https://icalendar.org>`_ to STDOUT. These can be
uploaded to Google Calendar, Outlook etc. An option is provided to include "all
day events" such as days off::

  $ aims ical --ade < aims_roster

Each entry has an identifier built from the start time of the duty and a list of
airports involved or, for all day events, the date and description of the duty.
This means that re-uploading an iCalendar file should update your calendar
correctly; there is, however, no mechanism for removing entries that have been
deleted from your roster since the last upload, so this will have to be done
manually.

CSV output
----------

::

   $ aims csv < aims_roster

Writes a comma separated value file following Excel conventions to STDOUT. This
can be used as a basis for getting data in to a spreadsheet based logbook — all
mainstream spreadsheets are capable of importing Excel CSV files.

Roster output
-------------

::

   $ aims roster < aims_roster

Outputs a roster in a text based diary format. Output looks something like
this::

  11/02/2024 06:00-12:34 BRS-ADTY-GVA-BRS 3:20/6:34
  26/02/2024 06:35-15:00 BRS-AMS-BRS-GLA-BRS 5:15/8:25
  27/02/2024 04:30-12:30 ESBY 0:00/8:00
  28/02/2024 08:00-16:00 OLAD 0:00/8:00

The two durations at the end of the line are the expected block hours and
expected duty hours. I use this format with emacs diary mode and to produce
predictive FTL charts.
