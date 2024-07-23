"""Processes the data extracted from a 'vertical' HTML AIMS roster.

The module's public interface is the duties() function, which accepts "soup" as
produced by processing the roster with BeautifulSoup.
"""

import datetime as dt
from typing import Optional

from aims.data_structures import Duty, Sector, CrewMember, InputFileException


Row = tuple[tuple[str, ...], ...]

# column indices
DATE, CODES, DETAILS, DSTART, TIMES, DEND, BHR, DHR, IND, CREW = range(1, 11)


def _convert_datestring(in_: str) -> dt.date:
    return dt.datetime.strptime(in_.split()[0], "%d/%m/%Y").date()


def _convert_timestring(in_: str, date: dt.date) -> dt.datetime:
    if in_[-2:] == "⁺¹":
        in_ = in_[:-2]
        date = date + dt.timedelta(1)
    time = dt.datetime.strptime(in_.replace("A", ""), "%H:%M").time()
    return dt.datetime.combine(date, time)


def _sectors(data: Row, date: dt.date) -> tuple[Sector, ...]:
    retval = []
    for c, code in enumerate(data[CODES]):
        code_split = code.split()
        name = code_split[0]
        type_ = None
        if len(code_split) == 2 and code_split[1][0] == "[":
            type_ = code_split[1][1:-1]
        airports = [X.strip() for X in data[DETAILS][c].split(" - ")]
        times = data[TIMES][c].split("/")[0].split(" - ")
        crew = []
        for m in data[CREW]:
            strings = m.split(" - ")
            if len(strings) >= 3:
                if strings[1] == "PAX":
                    continue
                crew.append(CrewMember(strings[-1], strings[0]))
            else:
                crew[-1] = CrewMember(crew[-1].name + " " + strings[0],
                                      crew[-1].role)
        if len(airports) == 2:  # Not an all day event or unused standby
            position = False
            if airports[0][0] == "*":  # Either ground or air positioning
                airports[0] = airports[0][1:]
                position = True
            quasi = not type_  # If no type in code, assume quasi sector
            retval.append(
                Sector(name, None, type_, airports[0], airports[1],
                       _convert_timestring(times[0], date),
                       _convert_timestring(times[1], date),
                       quasi, position, tuple(crew)))
        else:
            retval.append(
                Sector(name, None, None, None, None,
                       _convert_timestring(times[0], date),
                       _convert_timestring(times[1], date),
                       True, False, tuple(crew)))
    return tuple(retval)


def _duty(row: Row) -> Optional[Duty]:
    """Process a stringified row of the HTML table into the Duty it represents.

    Each row is a 12 item tuple. The first and last items are empty tuples
    since the original table has empty cells at the beginning and end of the
    row. In between these are tuples of strings; these come from splitting the
    strings in the original cells on newlines.

    The items in the row, from index 1 to index 10 are:

        1:  Date
        2:  Flight numbers plus aircraft type in square brackets or
            quasi sector type code (e.g. standby, taxi, ...)
        3:  Routes or description of quasi sector or all day duty
        4:  Report time. This is not necessarily duty start time -- there may
            be standby duties before report, and it is empty for standbys
            without a call out.
        5:  Sector times, including for quasi sectors. Empty for all day.
        6:  Duty end time. Empty for standby without callout.
        7:  Block hours
        8:  Duty hours
        9:  Markers for memos etc.
        10: Crew list. This is one of the weaknesses of this format -- the crew
            is associated with the entire duty rather than for each sector.

    :param row: A 12 cell tuple, with each cell a tuple of strings.
    :return: The Duty object represented by the row.
    """
    try:
        if not row[CODES]:
            return None
        date = _convert_datestring(row[DATE][0])
        # if there are no times, it is an all day event
        if not row[TIMES]:
            return Duty(row[CODES][0],
                        dt.datetime.combine(date, dt.time()),
                        None, ())
        # If duty start/finish does not exist, take the times from
        # the only sector. Details will be recorded in Duty.sectors.
        if row[DSTART]:
            start = _convert_timestring(row[DSTART][0], date)
            end = _convert_timestring(row[DEND][0], date)
        else:
            assert len(row[TIMES]) == 1
            times = row[TIMES][0].split(" - ")
            start = _convert_timestring(times[0], date)
            end = _convert_timestring(times[1], date)
        sectors = _sectors(row, date)
        # on duty can be before report if quasi sectors at start
        for sector in sectors:
            if not sector.quasi:
                break
            start = min(start, sector.off)
            end = max(end, sector.on)
        return Duty(None, start, end, sectors)
    except (IndexError, ValueError):
        raise InputFileException(f"Bad Record: {str(row)}")


def duties(soup) -> tuple[Duty, ...]:
    """Create a tuple of Duty objects from a BeautifulSoup of a roster.

    The important part of the roster is in the form of a large HTML table, with
    each row of the table representing a single duty. Whilst the header is a
    date, if duties continue past midnight, those times are marked with a
    superscript '+1' rather than being pushed to the next day, which makes it
    much saner to parse than the alternatives.

    :param soup: The soup of a 'vertical' HTML AIMS roster, as produced by
               processing the HTML with BeautifulSoup.
    :return: A tuple of Duty objects encoding the roster in a standard form.

    """
    rows = iter(soup.find_all("tr"))
    try:
        while "Schedule Details" not in next(rows).stripped_strings:
            pass
        next(rows)
        retval: list[Duty] = []
        while True:
            strings = tuple(
                tuple(Y.replace("\xa0", " ") for Y in X.stripped_strings)
                for X in next(rows)("td"))
            if not strings[DATE]:  # line without date ends table
                break
            if duty := _duty(strings):
                retval.append(duty)
    except (StopIteration, IndexError):
        raise InputFileException("Duty table ended unexpectedly")
    return tuple(retval)
