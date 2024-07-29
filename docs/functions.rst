
Processing Functions
====================

.. currentmodule:: aims.roster

.. function:: duties(html: str) -> tuple[tuple[Duty, ...], tuple[AllDayEvent, ...]]

   Produces a tuple of :class:`aims.data_structures.Duty` objects and a tuple of
   :class:`aims.data_structures.AllDayEvent` objects from the html of a vertical
   AIMS Crew Schedule.

   :param html: The HTML of a vertical AIMS crew schedule
   :return: A tuple consisting of a tuple of :class:`aims.data_structures.Duty`
            objects and a tuple of :class:`aims.data_structures.AllDayEvent`
            objects.

.. currentmodule:: aims.logbook_report

.. function:: duties(html: str) -> tuple[tuple[Duty, ...], tuple[AllDayEvent, ...]]

   Produce a tuple of :class:`aims.data_structures.Duty` from an the html of an
   AIMS Pilot Logbook report.

   :param html: The HTML of an AIMS Pilot Logbook report.
   :return: A tuple consisting of a tuple of :class:`aims.data_structures.Duty`
            objects and an empty tuple. The empty tuple is due to maintaining
            the same function signature as :func:`aims.roster.duties` and there
            being no all day events recorded in the Logbook report

.. currentmodule:: aims.parse

.. function:: parse(html: str) -> tuple[tuple[Duty, ...], tuple[AllDayEvent, ...]]

   Do some basic checks on the HTML, then attempt to identify whether it is an
   AIMS Crew Schedule or an AIMS Pilot Logbook report. If identification is
   successful, return the results of routing it to the correct
   :func:`duties` function.

   :param str html: The text of the HTML file being processed.
   :return: A tuple of :class:`aims.data_structures.Duty` objects and
      a tuple of :class:`aims.data_structures.AllDayEvent` objects
