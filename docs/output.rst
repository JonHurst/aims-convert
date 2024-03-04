Output Functions
================

.. currentmodule:: aims.output

.. function:: efj(sectors: tuple[Sector, ...], crewdict: CrewDict) -> str

   Transform to text with the `electronic Flight Journal (eFJ) scheme
   <https://hursts.org.uk/efjdocs/format.html#overview>`_.

   As well as converting the sector and crew information into the correct form,
   a night calculation is carried out (assuming that standard three letter codes
   are used for the airports) and, for easyJet pilots, the registration and type
   of the aircraft is looked up.

   Where the aircraft is unknown (e.g. non easyJet pilot or a very recent
   flight), the aircraft is output as ``?‑????:???``.

   :param sectors: A tuple of :class:`aims.roster.Sector` objects, as output by
                   :func:`aims.roster.sectors`.
   :param crewdict: A :data:`aims.roster.CrewDict` object, which is a dictionary of crew
                    members with sector identifiers as keys, as output by
                    :func:`aims.roster.crew_dict`.
   :return: Text with the eFJ scheme


.. function:: ical(sectors: tuple[Sector, ...], all_day_events: tuple[DayEvent, ...]) -> str

   Transform to `iCalendar format  <https://icalendar.org>`_.

   :param sectors: A tuple of :class:`aims.roster.Sector` objects, as output by
                   :func:`aims.roster.sectors`.
   :param all_day_events: a tuple of :data:`aims.roster.DayEvent` objects, as
                          output by :func:`aims.roster.all_day_events`.
   :return: Text in iCalendar format


.. function:: csv(sectors: tuple[Sector, ...], crewdict: CrewDict) -> str

   Transform to comma separated values with Excel flavour.

   The fields provided are 'Off Blocks', 'On Blocks', 'Duration', 'Night', 'Origin',
   'Destination', 'Registration', 'Type', 'Captain', and 'Crew'.

   :param sectors: A tuple of :class:`aims.roster.Sector` objects, as output by
                   :func:`aims.roster.sectors`.
   :param crewdict: A :data:`aims.roster.CrewDict` object, which is a dictionary of crew
                    members with sector identifiers as keys, as output by
                    :func:`aims.roster.crew_dict`.
   :return: Text in Excel flavoured CSV format.


.. function:: roster(sectors: tuple[Sector, ...]) -> str

   Transform to text format suitable for emacs diary and FTL prediction.

   Output looks something like this::

     11/02/2024 06:00-12:34 BRS-ADTY-GVA-BRS 3:20/6:34
     26/02/2024 06:35-15:00 BRS-AMS-BRS-GLA-BRS 5:15/8:25
     27/02/2024 04:30-12:30 ESBY 0:00/8:00
     28/02/2024 08:00-16:00 OLAD 0:00/8:00

   The two durations at the end of the line are the expected block hours and
   expected duty hours.

   :param sectors: A tuple of :class:`aims.roster.Sector` objects, as output by
                   :func:`aims.roster.sectors`.
   :return: Text suitable for emacs diary.
