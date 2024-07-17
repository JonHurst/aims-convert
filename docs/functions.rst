
Processing Functions
====================

.. currentmodule:: aims.roster

.. function:: duties(soup) -> tuple[Duty, ...]

   Create a tuple of :class:`aims.data_structures.Duty` extracted from a
   vertical AIMS Crew Schedule.

    :soup: The soup of the Crew Schedule, as created by parsing the html with
           BeautifulSoup4.
    :return: A tuple of :class:`aims.data_structures.Duty` objects.

.. currentmodule:: aims.logbook_report

.. function:: duties(soup) -> tuple[Duty, ...]

   Create a tuple of :class:`aims.data_structures.Duty` extracted from an
   AIMS Pilot Logbook report.

    :soup: The soup of the report, as created by parsing the html with
           BeautifulSoup4.
    :return: A tuple of :class:`aims.data_structures.Duty` objects.

.. currentmodule:: aims.parse

.. function:: parse(html) -> tuple[Duty, ...]

   Do some basic checks on the HTML, then attempt to identify whether it is an
   AIMS Crew Schedule or an AIMS Pilot Logbook report. If identification is
   successful, return the results of routing it to the correct
   :func:`duties` function.

   :html: The text of the HTML file being processed.
   :return: A tuple of :class:`aims.data_structures.Duty` objects.
