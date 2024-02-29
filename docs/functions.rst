
Roster Processing Functions
===========================

.. currentmodule:: aims.roster()


.. function:: lines(roster: str) -> tuple[Line, ...]

   Convert an AIMS roster into a tuple of :data:`Line` objects.

   An AIMS roster is fundamentally a very complex HTML table. Each :data:`Line`
   object represents a row of that table, and each string contained in the
   :data:`Line` object represents the contents of a table cell.

   :param roster: A string containing the HTML of an AIMS detailed roster.
   :return: A tuple of Line objects representing the text of the roster.


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
