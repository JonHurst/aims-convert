from bs4 import BeautifulSoup  # type: ignore

from aims.data_structures import Duty, AllDayEvent, InputFileException
import aims.roster
import aims.logbook_report


def parse(html: str) -> tuple[tuple[Duty, ...], tuple[AllDayEvent, ...]]:
    # check it's an html5 file
    html5_header = "<!DOCTYPE html><html>"
    if html[:len(html5_header)] != html5_header:
        raise InputFileException("HTML5 header not found.")
    # make some soup
    soup = BeautifulSoup(html, "html5lib")
    # route the soup
    strings = list(soup.find("body").stripped_strings)
    if "Personal Crew Schedule Report" in strings:
        return (aims.roster.duties(soup),
                aims.roster.all_day_events(soup))
    elif "Pilot Logbook" in strings:
        return (aims.logbook_report.duties(soup), ())
    else:
        raise InputFileException(
            "Report marker not found: \n" +
            "; ".join(strings[:20]))
