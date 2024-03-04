
Roster Processing Functions
===========================

.. currentmodule:: aims.roster


.. function:: lines(roster: str) -> tuple[Line, ...]

   Convert an AIMS roster into a tuple of :data:`Line` objects.

   An AIMS roster is fundamentally a very complex HTML table. Each :data:`Line`
   object represents a row of that table, and each string contained in the
   :data:`Line` object represents the contents of a table cell.

   :param roster: A string containing the HTML of an AIMS detailed roster.
   :return: A tuple of :data:`Line` objects representing the text of the roster.


.. function:: columns(lines: tuple[Line, ...]) -> tuple[Column, ...]

   Extract the main table in the form of a tuple of :data:`Column` objects.

   When an AIMS roster is viewed in a browser, each column of the main table
   represents a day. Groups of related cells are separated vertically by blank
   cells. Each group represents either a full day event, a sector, or, if a
   sector straddles midnight, part of a sector. Standby and positioning duties
   are considered to just be special forms of a sector.

   The columns function converts each group of cells into a :data:`DataBlock`,
   converting time strings to datetime objects in the process. The DataBlocks
   for a day are then joined into a tuple, and this is paired with the date
   pertaining to the column to form a :data:`Column` object. The :data:`Column`
   object structure is thus a very natural representation of a single column of
   the main table, as viewed in a browser. All the :data:`Column` objects are
   then joined into a tuple to represent the whole table.

   :param lines: An AIMS roster in the form output from the :func:`lines`
                 function.
   :return: A tuple of :data:`Column` objects, one :data:`Column` for each day
            covered by the roster.


.. function:: sectors(columns: tuple[Column, ...]) -> tuple[Sector, ...]

   Process the main table of an AIMS roster from a tuple of :data:`Column`
   objects into a tuple of :class:`Sector` objects.

   Each :data:`DataBlock` is classified as being a sector, a quasi sector or an
   all day event. All day events are dropped, and everything else is converted
   to a :class:`Sector` object. The :attr:`Sector.from_` and :attr:`Sector.to`
   fields are set to ``None`` for quasi sectors.

   Data Blocks that straddle columns are handled. Data Blocks that straddle the
   beginning and end of the table (i.e. they have some of their data missing)
   are recorded with default values for the missing data. There are some cases
   where it is not possible to correctly identify missing data.

   :param columns: A tuple of :data:`aims.roster.Column` objects representing
                   the main table of the roster, as produced by
                   :func:`aims.roster.columns`.
   :return: A tuple of :class:`aims.roster.Sector` objects containing all the
            sectors and quasi sectors extracted from the table.


.. function:: duties(sectors: tuple[Sector, ...]) -> tuple[Duty, ...]

    Group sectors into duties.

    Sector are considered to be part of the same duty if the time elapsed
    between on chocks for one sector and off chocks for the next is less than 11
    hours. This accounts for two consecutive airport standbys (i.e. no
    pre/post duty time required) being separate duties with minumum rest
    between.

    :param sectors: The tuple of :class:`Sector` objects to be grouped, sorted
        by off chocks time
    :return: A sorted tuple of :class:`Duty` objects with the input sectors
        grouped and duty start and finish times extracted.


.. function:: crew_dict(lines: tuple[Line, ...]) -> CrewDict

   Build mapping of crew members to sectors.

   :param lines: A tuple of :data:`Line` objects as output by the :func:`lines`
                 function.
   :return: A :data:`CrewDict` object. This maps a tuple of :data:`CrewMember`
            objects to a (date, flight number) pair or a (date, None) pair if
            the roster used the "All" code. To find all crew associated with a
            sector requires checking both keys.


.. function:: all_day_events(columns: tuple[Column, ...]) -> tuple[DayEvent, ...]

    Extract all day events from a tuple of Columns

    Simple all day events are shown on the roster as a single string at the top
    of the column. An all day event may also, however, occur after a duty, in
    which case it can be an isolated string at any point in the column.
    Unfortunately, indicators also take this form on the roster; we assume one
    and two character strings are indicators as a best effort.

    Things like SNCR are presented on the roster identically to things like
    days off, so we treat these as also being all day events.

    The possibility exists, although I have never seen it on a roster, that two
    all day events will be presented as two strings withouth a gap between.
    Since this shouldn't happen for any blocks representing sectors or quasi
    sectors, if it occurs each string is considered a separate all day event.

    :param columns: A tuple of :data:`aims.roster.Column` objects to process
    :return: A tuple of :data:`aims.roster.DayEvent` objects
