Type Aliases
============

.. currentmodule:: aims.roster

.. data:: Line
   :type: TypeAlias

   Alias for ``tuple[str, ...]``

.. data:: Datum
   :type: TypeAlias

   Alias for ``Union[str, datetime.datetime]``

.. data:: DataBlock
   :type: TypeAlias

   Alias for ``tuple[Datum, ...]``

.. data:: Column
   :type: TypeAlias

   Alias for ``tuple[datetime.date, tuple[DataBlock, ...]]``

.. data:: DayEvent
   :type: TypeAlias

   Alias for ``tuple[datetime.date, str]``

.. data:: CrewList
   :type: TypeAlias

   Alias for ``tuple[CrewMember, ...]``

.. data:: CrewDict
   :type: TypeAlias

   Alias for ``dict[tuple[datetime.date, Optional[str]], CrewList]``. The key
   can be used to look up the crew associated with a sector by first examining
   the exact sector using the date and sector name and if that fails examining
   all sectors on that day by using ``None`` for the sector name.
