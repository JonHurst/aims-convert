Exceptions
==========

.. currentmodule:: aims.roster

.. exception:: RosterException

   The base class for exceptions generated while parsing an AIMS roster.

.. exception:: InputFileException

   Generated when the input file does not appear to be an AIMS detailed roster.

..
   .. exception:: SectorFormatException

      Generated when parsing of a sector fails. This probably means that there is
      some quirk that rostering have come up with that has not yet been accounted
      for.

   .. exception:: CrewFormatException

      Generated when the crew section of an AIMS detailed roster is not in the
      expected format.
