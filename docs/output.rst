Output Functions
================

.. currentmodule:: aims.output

.. function:: efj(duties: tuple[Duty, ...]) -> str

   Transform to text with the `electronic Flight Journal (eFJ) scheme
   <https://hursts.org.uk/efjdocs/format.html#overview>`_.

   As well as converting the duty, sector and crew information into the correct
   form, a night calculation is carried out (assuming that standard three letter
   codes are used for the airports).

   :param duties: A tuple of :class:`aims.data_structures.Duty` objects, as output by
                   :func:`aims.parse.parse`.
   :return: Text with the eFJ scheme


.. function:: ical(duties: tuple[Duty, ...], ade: tuple[AllDayEvent, ...]) -> str

   Transform to `iCalendar format  <https://icalendar.org>`_.

   :param duties: A tuple of :class:`aims.data_structures.Duty` objects, as output by
                   :func:`aims.parse.parse`.
   :param ade: A tuple of :class:`aims.data_structures.AllDayEvent` objects, as
               output by :func:`aims.parse.parse`.
   :return: Text in iCalendar format


.. function:: csv(duties: tuple[Duty, ...]) -> str

   Transform to comma separated values with Excel flavour.

   The fields provided are 'Off Blocks', 'On Blocks', 'Duration', 'Night', 'Origin',
   'Destination', 'Registration', 'Type', 'Captain', and 'Crew'.

   :param duties: A tuple of :class:`aims.data_structures.Duty` objects, as output by
                   :func:`aims.parse.parse`.
   :return: Text in Excel flavoured CSV format.


.. function:: roster(duties: tuple[Duty, ...]) -> str

   Transform to text format suitable for emacs diary and FTL prediction, with
   times in UK local.

   Output looks something like this::

     11/02/2024 06:00-12:34 BRS-ADTY-GVA-BRS 3:20/6:34
     26/02/2024 06:35-15:00 BRS-AMS-BRS-GLA-BRS 5:15/8:25
     27/02/2024 04:30-12:30 ESBY 0:00/8:00
     28/02/2024 08:00-16:00 OLAD 0:00/8:00

   The two durations at the end of the line are the expected block hours and
   expected duty hours.

   :param duties: A tuple of :class:`aims.data_structures.Duty` objects, as output by
                   :func:`aims.parse.parse`.
   :return: Text suitable for emacs diary.
