# AIMS Roster Data Extraction #

This will primarily be of interest to easyJet pilots. It extracts data from a
reports that can be downloaded from AIMS. Pilots from other airlines that use
AIMS *may* also find this useful — it has only been tested against the files
from easyJet’s version of AIMS (as that is all that I have access to), so its
utility will depend on whether whatever version is being used by your airline
produces sufficiently similar output.

As well as extracting the data, a night flying calculation is carried out.

The three main formats that the data can be extracted to are electronic Flight
Journal (eFJ), iCalendar and CSV.

An eFJ is a text file that can be used to store personal flight data in an
intuitive non-tabular form. Full details of the format of this text file can be
found at <https://hursts.org.uk/efjdocs/format.html>, and an online tool
capable of converting this format to an FCL.050 compliant logbook in HTML
format can be found at <https://hursts.org.uk/efj>.

The iCalendar format can be imported into most calendar applications. There is
an option to include full day events such as days off. This is useful for
managing and sharing your future roster.

The CSV format is for keeping logbook data in a spreadsheet.

The package provides entry points for a command line interface, a Tk based
graphical interface and an AWS lambda function. The AWS function is hooked up
to a website at <https://hursts.org.uk/aims>, which requires no installation,
just a browser. The other two interfaces require the installation of a Python
interpreter.
