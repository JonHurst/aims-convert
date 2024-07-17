
Processing Functions
====================

.. currentmodule:: aims.roster

.. function:: duties(soup) -> tuple[Duty, ...]

   Create a tuple of :class:`aims.data_structures.Duty` extracted from a
   vertical AIMS Crew Schedule.

   :param soup: The soup of the Crew Schedule, as created by parsing the html with
                BeautifulSoup4.
   :return: A tuple of :class:`aims.data_structures.Duty` objects.

.. currentmodule:: aims.logbook_report

.. function:: duties(soup) -> tuple[Duty, ...]

   Create a tuple of :class:`aims.data_structures.Duty` extracted from an
   AIMS Pilot Logbook report.

   :param soup: The soup of the report, as created by parsing the html with
                     BeautifulSoup4.
   :return: A tuple of :class:`aims.data_structures.Duty` objects.

.. currentmodule:: aims.parse

.. function:: parse(html: str) -> tuple[Duty, ...]

   Do some basic checks on the HTML, then attempt to identify whether it is an
   AIMS Crew Schedule or an AIMS Pilot Logbook report. If identification is
   successful, return the results of routing it to the correct
   :func:`duties` function.

   :param str html: The text of the HTML file being processed.
   :return: A tuple of :class:`aims.data_structures.Duty` objects.
