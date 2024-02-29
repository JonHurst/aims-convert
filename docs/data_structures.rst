Named Tuples
============

.. class:: Sector

   A Named Tuple representing a sector or a quasi sector such as standby,
   positioning etc.

   .. attribute:: name
   :type: str

   Either the flight number of a sector or a string describing the type of a
   quasi sector (e.g. STBY, ADTY).

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

   .. attribute:: src
   :type: DataBlock

   The data from which the object was created.
