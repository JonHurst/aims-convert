from bs4 import BeautifulSoup  # type: ignore

from aims.data_structures import Duty, InputFileException
import aims.roster
import aims.logbook_report


def parse(html: str) -> tuple[Duty, ...]:
    # check it's an html5 file
    html5_header = "<!DOCTYPE html><html>"
    if html[:len(html5_header)] != html5_header:
        raise InputFileException
    # make some soup
    soup = BeautifulSoup(html, "html5lib")
    # route the soup
    if "Personal Crew Schedule Report" in soup.find("body").stripped_strings:
        return aims.roster.duties(soup)
    elif "Pilot Logbook" in soup.find("body").stripped_strings:
        return aims.logbook_report.duties(soup)
    else:
        raise InputFileException
