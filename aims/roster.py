"""Extracts data from a 'vertical' HTML AIMS roster."""
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
    """Extract sector data from a row.

    The CODES field contains a string for each flying sector or quasi sector.
    For flying sectors the string is of the form "1234 [320]" where 1234 is the
    flight number and 320 is the type. For quasi sectors, it is the sector code
    such as "ADTY".

    For each string in the CODES field there is an equivalent string with the
    same index in the DETAILS and TIMES fields.

    In the DETAILS field the strings are mainly airport pairs. These have the
    form form "ABC - XYZ", where each is a 3 letter airport code. Where the
    sector is a positioning sector, a "*" is prepended. Quasi sectors may have
    the same airport in both halves of the pair, e.g. "LGW - LGW" for a sim.
    Where the duty consists of a single quasi sector this field can instead
    contain a textual description of the type of quasi sector.

    In the TIMES field, the basic form is "13:00 - 14:00". Each half may also
    be prepended with an "A" representing an "actual" time or an "E"
    representing an "estimated" time, although this is not done consistently.
    The final string in the series may also have a delay of the form "/00:10"
    appended to it.

    The CREW field contains the crew for the entire duty. It is described in
    the docstring of the _crew function. There is no way of discerning which
    crewmembers operated which sectors, although this is not usually a huge
    problem -- crew changes during a duty are not particularly common, and
    including the full set for every sector makes it easy to manually adjust
    the output if required. It can be assumed that quasi sectors have no crew.

    :param data: A Row representing a single duty. It is assumed that Row
        structures representing all day events are not passed to this function.
    :return: A tuple of Sector objects

    """
    assert data[CODES] and data[TIMES] and data[DETAILS]
    retval = []
    crew = _crew(data[CREW])
    for c, code in enumerate(data[CODES]):
        code_split = code.split()
        name = code_split[0]
        type_ = None
        if len(code_split) == 2 and code_split[1][0] == "[":
            type_ = code_split[1][1:-1]
        airports = [X.strip() for X in data[DETAILS][c].split(" - ")]
        times = data[TIMES][c].split("/")[0].split(" - ")
        if len(airports) == 2:
            position = False
            if airports[0][0] == "*":  # Either ground or air positioning
                airports[0] = airports[0][1:]
                position = True
            quasi = not type_  # If no type in code, assume quasi sector
            retval.append(
                Sector(name, None, type_, airports[0], airports[1],
                       _convert_timestring(times[0], date),
                       _convert_timestring(times[1], date),
                       quasi, position, () if quasi else crew))
        else:  # unused standby
            retval.append(
                Sector(name, None, None, None, None,
                       _convert_timestring(times[0], date),
                       _convert_timestring(times[1], date),
                       True, False, ()))
    return tuple(retval)


def _duty(row: Row) -> Duty:
    """Creates a Duty object from a structured representation of an HTML row.

    The input object is a variable length tuple with each cell containing the
    contents of a "td" from the original HTML row in the form of a variable
    length tuple of strings; this is a result of the original contents of the
    cells potentially being multi-line.

    The cells in the row, from index 1 to index 10 are:

    1: DATE: Date of the form "01/01/2000 Mon", which may be split over two
       lines at the space.

    2: CODES: Described in the docstring of the _sectors function.

    3: DETAILS: Described in the docstring of the _sectors function.

    4: DSTART: Report time. This is not necessarily duty start time -- there
       may be standby duties etc. before report. Empty for standbys without a
       call out.

    5: TIMES: Described in the docstring of the _sectors function.

    6: DEND: Duty end time. Empty for standby without callout.

    7: BHR: Block hours

    8: DHR: Duty hours

    9: IND: Markers for memos etc.

    10: CREW: Described in the docstring of the _crew function.

    :param row: A variable length tuple that has filled CODES and TIMES fields.
        Each cell a tuple of strings, one per line of the original <td>.
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
            # the sectors.
            times = row[TIMES][0].split(" - ")
            start = _convert_timestring(times[0], date)
            times = row[TIMES][-1].split(" - ")
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
    """Extract an all day event.

    All fields other than the DATE, CODES and DETAILS are empty for all day
    events. The DETAILS field is just a textual description, and the CODES
    field should only have one line.

    :param row: A variable length tuple with a tuple containing a single string
        in the CODES field.
    :return: An AllDayEvent object extracted from the row.

    """
    try:
        return AllDayEvent(_convert_datestring(row[DATE][0]), row[CODES][0])
    except (IndexError, ValueError):
        raise InputFileException(f"Bad All Day Duty Record: {str(row)}")


def duties(html: str) -> tuple[tuple[Duty, ...], tuple[AllDayEvent, ...]]:
    """Extract the data from an AIMS vertical roster.

    The entire document is a single table (how retro!). The interesting part
    starts with the row two rows below the row with a cell containing the
    phrase "Schedule Details" and ends with the row above the first subsequent
    row with a blank DATE field. Everything between, therefore, should have a
    filled DATE field.

    Each row can represent:

    1: An unpublished duty. The marker for this is an empty CODES field.

    2: An all day event. The marker for this is a filled CODES field and an
    empty TIMES field. These are described in the docsting of the _ade()
    function.

    3: A normal duty. If neither of the above are true, the row represents a
    duty with a start and an end time. These are described in the docstring
    of the _duty() function.

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
            else:  # a normal duty
                duty_list.append(_duty(row))
        return (tuple(duty_list), tuple(ade_list))
    except (StopIteration, IndexError):
        raise InputFileException("Duty table ended unexpectedly")
