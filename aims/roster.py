"""Processes the data extracted from a 'vertical' HTML AIMS roster.

The module's public interface is the duties() function, which accepts "soup" as
produced by processing the roster with BeautifulSoup.
"""

import datetime as dt
import re

from bs4 import BeautifulSoup  # type: ignore

from aims.data_structures import (
    Duty, Sector, CrewMember, AllDayEvent, InputFileException)


Row = tuple[tuple[str, ...], ...]

# column indices
DATE, CODES, DETAILS, DSTART, TIMES, DEND, BHR, DHR, IND, CREW = range(1, 11)


def _convert_datestring(in_: str) -> dt.date:
    return dt.datetime.strptime(in_.split()[0], "%d/%m/%Y").date()


def _convert_timestring(in_: str, date: dt.date) -> dt.datetime:
    if in_[-2:] == "⁺¹":
        in_ = in_[:-2]
        date = date + dt.timedelta(1)
    in_ = in_.replace("A", "").replace("E", "")
    time = dt.datetime.strptime(in_, "%H:%M").time()
    return dt.datetime.combine(date, time)


def _crew(strings: tuple[str, ...]) -> tuple[CrewMember, ...]:
    """Convert crew cell to a tuple of CrewMember objects.

    Each string may either represent a crew member or be a continuation of a
    crew member's name if the details didn't all fit on one line. In the first
    case the line will start with "CP -", "FO -" etc. The line is split on a
    space if it is split.

    For postioning crew, the string has the form "CP - PAX - 1234 - NAME MY".
    Positioning crew should not be included in the crew list.

    :param strings: The tuple of strings from the crew field of a duty record.
    :return: A tuple of CrewMember objects.

    """
    re_first = re.compile(r"[A-Z]{2} - ")
    joined_strings: list[str] = []
    for s in strings:
        if re_first.match(s):
            joined_strings.append(s)
        else:
            joined_strings[-1] += f" {s}"
    crew: list[CrewMember] = []
    for j in joined_strings:
        fields = j.split(" - ")
        if len(fields) < 3:
            raise InputFileException("Bad crew block")
        if fields[1] != "PAX":
            crew.append(CrewMember(fields[-1], fields[0]))
    return tuple(crew)


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
        crew = _crew(data[CREW])
        if len(airports) == 2:  # Not an all day event or unused standby
            position = False
            if airports[0][0] == "*":  # Either ground or air positioning
                airports[0] = airports[0][1:]
                position = True
            quasi = False
            if not type_:  # If no type in code, assume quasi sector
                quasi = True
                crew = ()
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


def _duty(row: Row) -> Duty:
    """Creates a Duty object from a structured representation of an HTML row.

    The input object is a 12 cell tuple with each cell containing the contents
    of a "td" from the original HTML row. The contents are in the form of a
    variable length tuple of strings since the original contents of the cells
    can be multi-line. The first and last items are empty tuples since the
    original table has empty cells at the beginning and end of each row.

    The items in the row, from index 1 to index 10 are:

    1: Date of the form "01/01/2000 Mon", which may be split over two lines at
       the space.

    2: Either:

       + An empty tuple for an unpublished duty; or

       + For all day duties, the code for the all day duty; or

       + For normal sectors, the flight number plus aircraft type in square
         brackets e.g. "1234 [320]", one for each sector in the duty; or

       + For quasi sectors, the code of the quasi sector (e.g. "ESBY", "ADTY",
         "TAXI123"), one for each quasi sector in the duty. These can be mixed
         in with normal sectors.

    3: Either:

       + For all day duties, a textual description of the duty; or

       + For sectors, the airports invloved in the form "BRS - FNC", one for
         each sector or quasi sector in the duty. For quasi sectors the two
         airports may be the same (e.g. "LGW - LGW" for a sim) or, to indicate
         postioning, may start with a "*" (e.g "*LGW - BRS" for a taxi ride).

    4: Report time. This is not necessarily duty start time -- there may be
       standby duties before report, and it is empty for standbys without a
       call out.

    5: Sector times of the form "11:00 - 13:00", one for each sector in the
       duty, including for quasi sectors. For duties that have already taken
       place, the fact that the times are actual times may be indicated with an
       "A", giving the form "A11:00 - A13:00", although this doesn't seem to be
       especially consistently done. The string for the last sector may also
       incorporate the delay in the form "A11:00 - A13:00/01:00". For an all
       day duty there are no times to record, and hence the cell will be an
       empty tuple.

    6: Duty end time. Empty for standby without callout.

    7: Block hours

    8: Duty hours

    9: Markers for memos etc.

    10: Crew list, one string per crew member. The crew is associated with the
        entire duty rather than per sector.

    :param row: A 12 cell tuple, with each cell a tuple of strings.
    :return: The Duty object represented by the row.

    """
    try:
        assert row[CODES] and row[TIMES]
        date = _convert_datestring(row[DATE][0])
        if row[DSTART]:
            assert row[DEND]
            start = _convert_timestring(row[DSTART][0], date)
            end = _convert_timestring(row[DEND][0], date)
        else:
            # If duty start/finish does not exist, take the times from
            # the only sector.
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
        return Duty(start, end, sectors)
    except (IndexError, ValueError):
        raise InputFileException(f"Bad Duty Record: {str(row)}")


def _ade(row: Row) -> AllDayEvent:
    try:
        return AllDayEvent(_convert_datestring(row[DATE][0]), row[CODES][0])
    except (IndexError, ValueError):
        raise InputFileException(f"Bad All Day Duty Record: {str(row)}")


def duties(html: str) -> tuple[tuple[Duty, ...], tuple[AllDayEvent, ...]]:
    """Extract the data from an AIMS vertical roster.

    The entire document is a single table (how retro!). The interesting part
    starts with the row two rows below the row with a cell containing the
    phrase "Schedule Details" and ends with the row above the first row with a
    blank date field. Each row between these represents a single duty or an all
    dat event.

    The date to the left of each row is the date that the duty started on. If
    duties continue past midnight, relevant times are marked with a superscript
    '+1' rather than being pushed to the next row of the table. This makes the
    vertical roster much saner to parse than the alternatives since there are
    no concerns about missing data at the start and end of the roster period.

    :param html: The html of a 'vertical' HTML AIMS roster.
    :return: A tuple of Duty objects and a tuple of AllDayEvent objects

    """
    soup = BeautifulSoup(html, "html5lib")
    rows = iter(soup.find_all("tr"))
    try:
        while "Schedule Details" not in next(rows).stripped_strings:
            pass
        next(rows)
        duty_list: list[Duty] = []
        ade_list: list[AllDayEvent] = []
        while True:
            row: Row = tuple(
                tuple(Y.replace("\xa0", " ") for Y in X.stripped_strings)
                for X in next(rows)("td"))
            if not row[DATE]:  # line without date ends table
                break
            if not row[CODES]:  # unpublished duty
                continue
            if not row[TIMES]:  # an all day event
                ade_list.append(_ade(row))
            elif duty := _duty(row):  # a normal duty
                duty_list.append(duty)
        return (tuple(duty_list), tuple(ade_list))
    except (StopIteration, IndexError):
        raise InputFileException("Duty table ended unexpectedly")
