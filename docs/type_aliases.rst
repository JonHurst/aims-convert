Type Aliases
============

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
