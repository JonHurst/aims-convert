from aims.data_structures import Duty, AllDayEvent, InputFileException
import aims.roster
import aims.logbook_report


def parse(html: str) -> tuple[tuple[Duty, ...], tuple[AllDayEvent, ...]]:
    # check it's an html5 file
    html5_header = "<!DOCTYPE html><html>"
    if html[:len(html5_header)] != html5_header:
        raise InputFileException("HTML5 header not found.")
    if html.find("Personal&nbsp;Crew&nbsp;Schedule&nbsp;Report") != -1:
        return aims.roster.duties(html)
    elif html.find("Pilot&nbsp;Logbook") != -1:
        return aims.logbook_report.duties(html)
    else:
        raise InputFileException("Report type marker not found")
