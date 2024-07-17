Data Structures
===============

.. currentmodule:: aims.data_structures

.. class:: Sector

   A Named Tuple representing a sector or a quasi sector such as standby,
   positioning etc.

   .. attribute:: name
      :type: str

   Either the flight number of a sector or a string describing the type of a
   quasi sector (e.g. STBY, ADTY).

   .. attribute:: reg
      :type: Optional[str]

   The registration of the aircraft, if applicable.

   .. attribute:: type_
      :type: Optional[str]

   The type of the aircraft, if applicable.

   .. attribute:: from_
      :type: Optional[str]

   The origin airport, if applicable.

   .. attribute:: to
      :type: Optional[str]

   The destination airport, if applicable.

   .. attribute:: off
      :type: datetime.datetime

   Off blocks time or the start time of a standby, positioning duty etc.

   .. attribute:: on
      :type: datetime.datetime

   On blocks time or the end time of a standby, postitioning duty etc.

   .. attribute:: quasi
      :type: bool

   A flag indicating that the sector did not involve and aircraft, e.g. it was a
   standby or ground positioning.

   .. attribute:: position
      :type: bool

   A flag indicating that the sector was either ground or air positioning.



.. class:: Duty

   A Named Tuple representing a duty

   .. attribute:: start
      :type: datetime.datetime

   The start time of the duty. Can be the report time for a series of sectors or
   the start time of a standby, taxi ride etc.

   .. attribute:: finish
      :type: datetime.datetime

   The finish time for a duty.

   .. attribute:: sectors
      :type: tuple[Sector, ...]

   A (possibly empty) tuple of :class:`Sector` objects that are part of the duty.


.. class:: CrewMember

   A Named Tuple representing a crew member.

   .. attribute:: name
      :type: str

      The crew member's name.

   .. attribute:: role
      :type: str

      The crew member's role. Usually one of ``CP``, ``FO``, ``PU`` or ``FA``.
