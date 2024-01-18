#!/usr/bin/python3
import sys
import re
import datetime as dt
from html.parser import HTMLParser
from typing import Union, NamedTuple, Optional, cast
import itertools as it


Datum = Union[str, dt.datetime]
DataBlock = tuple[Datum, ...]
Column = tuple[dt.date, tuple[DataBlock, ...]]
Line = tuple[str, ...]
DayEvent = tuple[dt.date, str]


class Sector(NamedTuple):
    name: str
    from_: Optional[str]
    to: Optional[str]
    off: dt.datetime
    on: dt.datetime
    src: DataBlock


class Duty(NamedTuple):
    start: dt.datetime
    finish: dt.datetime
    sectors: tuple[Sector, ...]


class CrewMember(NamedTuple):
    name: str
    role: str


CrewList = tuple[CrewMember, ...]
CrewDict = dict[tuple[dt.date, Optional[str]], CrewList]


class RosterException(Exception):

    def __str__(self):
        return self.__doc__


class InputFileException(RosterException):
    "Input file does not appear to be an AIMS detailed roster."


class SectorFormatException(RosterException):
    "Sector with unexpected format found."


class CrewFormatException(RosterException):
    "Crew section with unexpected format found."


class RosterParser(HTMLParser):

    def __init__(self):
        self.output_list = [[]]
        self.in_td = False
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self.in_td = True
            self.output_list[-1].append("")
        elif tag == "br":
            if self.in_td:
                self.output_list[-1][-1] += "\n"

    def handle_endtag(self, tag):
        if tag == "td":
            self.in_td = False
        elif tag == "tr":
            self.output_list.append([])

    def handle_data(self, data):
        if self.in_td:
            self.output_list[-1][-1] += data


def lines(roster: str) -> tuple[Line, ...]:
    """Turn an AIMS roster into a tuple of Line objects.

    An AIMS roster is fundamentally a very complex HTML table. Each Line object
    represents a row of that table, and each string contained in the Line
    object represents the contents of a cell.

    :param roster: A string containing the HTML of an AIMS detailed roster.
    :return: A tuple of Line objects representing the text of the roster.
    """
    parser = RosterParser()
    parser.feed(roster)
    if (len(parser.output_list) < 10
            or len(parser.output_list[1]) < 1
            or not parser.output_list[1][0].startswith("Personal")):
        raise InputFileException
    return tuple(cast(Line, tuple(X)) for X in parser.output_list)


def columns(lines: tuple[Line, ...]) -> tuple[Column, ...]:
    """Extract the main table in the form of a tuple of Column objects.

    When an AIMS roster is viewed in a browser, each column of the main table
    represents a day. Groups of cells are separated vertically by blank cells,
    with. Each group represents either a full day event, a sector, or, if a
    sector straddles midnight, part of a sector. Standby and positioning duties
    are considered to just be special forms of a sector.

    The columns function converts each separate group into a DataBlock. Time
    strings to datetime objects in the process. All the DataBlocks are then
    formed into a tuple, and this is paired with the date of the column to form
    a Column object. The Column objects structure is thus a very natural
    representation of the column as viewed ia a browser.

    :param lines: An AIMS roster in the form output from the lines function.
    :return: A tuple of Column objects, one Column for each day covered by the
        roster.
    """
    mo = re.search(r"Period: (\d{2}/\d{2}/\d{4})", lines[1][0])
    if not mo:
        raise InputFileException
    start_date = dt.datetime.strptime(mo.group(1), "%d/%m/%Y").date()
    # assumption: main table starts on row 5 of the page 1 table
    width = len(lines[5])
    columns_as_strs: list[list[str]] = [[] for _ in range(width)]
    for line in lines[5:]:
        if len(line) != width:
            continue
        if "Block" in line:
            break  # The last line contains the word "Block"
        for c, entry in enumerate(line):
            columns_as_strs[c].append(entry.strip())
    retval: list[Column] = []
    for c, col_strings in enumerate(columns_as_strs):
        if not col_strings[0]:  # blank column head means we're done
            break
        col_date = start_date + dt.timedelta(c)
        p = _process_column(tuple(col_strings), col_date)
        retval.append((col_date, p))
    return tuple(retval)


def _process_column(
        col: tuple[str, ...], date: dt.date
) -> tuple[DataBlock, ...]:
    """Converts the strings found in a column into a tuple of DataBlocks. Input
    is split up on runs of empty strings, and anything of the form HH:MM is
    converted to a datetime.

    The "24:00" bug is also handled at this point by converting it to 00:00 on
    the following day.

    :param col: The Column to process.
    :param date: The date to apply to entries in the column
    :return: A list of StreamItems. Leading and trailing Breaks are removed.
    """
    assert all(isinstance(X, str) for X in col)
    converted: list[Datum] = []
    for entry in col[1:]:
        try:  # try to treat entry like a time
            time = dt.datetime.strptime(entry, "%H:%M").time()
            converted.append(dt.datetime.combine(date, time))
        except ValueError:  # if that fails, treat it like a string
            if entry == "24:00":
                bug_fix = (dt.datetime.combine(date, dt.time())
                           + dt.timedelta(1))
                converted.append(bug_fix)
            else:
                converted.append(entry)
    groups = filter(lambda x: x[0], it.groupby(converted, bool))
    return tuple(cast(DataBlock, tuple(X[1])) for X in groups)


def all_day_events(columns: tuple[Column, ...]) -> tuple[DayEvent, ...]:
    """Extract all day events from a tuple of Columns

    Simple all day events are shown on the roster as a single string at the top
    of the column. An all day event may also, however, occur after a duty, in
    which case it can be an isolated string at any point in the column.
    Unfortunately, indicators also take this form on the roster; we assume one
    and two character strings are indicators as a best effort.

    Things like SNCR are presented on the roster identically to things like
    days off, so we treat these as also being all day events.

    The possibility exists, although I have never seen it on a roster, that two
    all day events will be presented as two strings withouth a gap between.
    Since this shouldn't happen for any blocks representing sectors or quasi
    sectors, if it occurs each string is considered a separate all day event.

    :param columns: A tuple of Column objects to process
    :return: A tuple of DayEvent objects, a DayEvent being a tuple of the form
        (date, event_string)
    """
    retval: list[DayEvent] = []
    for col in columns:
        all_day_events_ = it.chain.from_iterable(filter(
            lambda block: all(isinstance(X, str) for X in block),
            col[1]))
        for event in all_day_events_:
            if len(cast(str, event)) > 2:
                retval.append((col[0], cast(str, event)))
    return tuple(retval)


def _search_standard_block(
        block: DataBlock
) -> tuple[str, dt.datetime, str, str, dt.datetime]:
    """Extract id, times and airfields from a DataBlock.

    The key assumptions are:

    1. That the first occasion when a string *follows* a datetime is when the
    string is the origin airport and the datetime is the off chocks time.

    2. That the occasion thereafter that a string is *followed by* a datetime
    is when the string is the destination airport and the datetime is the on
    chocks time.

    3. That the flight number is the nearest string above the origin airport.

    So far this has proved robust, but a lot of random cruft gets injected into
    rosters...

    If no origin airport is found, the sector is probably a quasi sector. If an
    origin airport is found but no destination airport is found, the sector
    probably straddled midnight, in which case the destination airport and on
    chocks time will be found in the next DataBlock in the stream.

    :param block: The DataBlock to be processed.
    :return: A tuple of the form (id, off, from, to, on). If not found, the
        return values of off and on are default values and the return values of
        id, from and to are empty strings.

    """
    id_, from_, to = "", "", ""
    off, on = dt.datetime(1970, 1, 1), dt.datetime(1970, 1, 1)
    str_mask = [isinstance(X, str) for X in block]
    it = iter(range(len(block) - 1))
    for c in it:
        if str_mask[c]:
            id_ = cast(str, block[c])
        elif str_mask[c + 1]:
            # found the marker for off and from
            off = cast(dt.datetime, block[c])
            from_ = cast(str, block[c + 1])
            next(it)  # skip from entry
            break
    if from_:
        for c in it:  # continue iterating from the entry after from
            if str_mask[c] and not str_mask[c + 1]:
                # found the marker for to and on
                to = cast(str, block[c])
                on = cast(dt.datetime, block[c + 1])
                break
    return (id_, off, from_, to, on)


def _extract_standard_sector(
        block: DataBlock, extra_block: DataBlock
) -> tuple[Optional[Sector], int]:
    """Try to extract a standard sector from a DataBlock, and if required, the
    following DataBlock

    :param block: The DataBlock to process
    :param extra_block: An extra block that will be searched for the
        destination and on chocks time if those are not found in the primary
        block.
    :return: If successful, the retrieved Sector and the number of blocks
        processed to find it. If unsuccessful, (None, 0).
    """
    src = block
    used = 1
    id_, off, from_, to, on = _search_standard_block(block)
    if from_ and not to:  # if "to" is  not found, try in the extra block
        for c in range(len(extra_block) - 1):
            if (isinstance(extra_block[c], str)
                    and isinstance(extra_block[c + 1], dt.datetime)):
                # found the marker for to and on
                to = cast(str, extra_block[c])
                on = cast(dt.datetime, extra_block[c + 1])
                break
        src = tuple(list(block) + list(extra_block))
        used = 2
    if not to:
        return (None, 0)
    # fix for dragover case
    if on - off > dt.timedelta(1):
        on -= dt.timedelta(1)
    return (Sector(id_, from_, to, cast(dt.datetime, off), on, src), used)


def _extract_quasi_sector(block: DataBlock) -> Optional[Sector]:
    """Try to extract a quasi sector (i.e a standby, LOE or suchlike) from a
    DataBlock.

    By the time this is called, any quasi sectors straddling midnight should
    have been merged into a single DataBlock (_columns_to_datastream does this
    early in proceedings).

    A block relating to a quasi sector has a string title followed by 2 to 4
    inclusive datetimes. Two is easy -- it's a standby on it's own, so we treat
    the two times as off and on chocks. Four is something like an LOE. We treat
    the inner pair as chock times and the outer pair as duty times. Three
    occurs with standby and training duties that form part of a series of
    sectors. Generally, the standby happens before other stuff, so we want the
    last two times for block times and the first gets treated as a duty report
    time.

    A corner case occurs when a standard sector is split over midnight at the
    start of the roster, so that only the end of the sector is shown. This is
    indistinguishable from a quasi sector, so it is treated as such. It could
    also have a dragover problem, so that the first datetime is actually on the
    previous day, so we fix this if it occurs as a best effort.

    :param block: The block to extract the quasi sector from.
    :return: None if unsuccessful. A Sector object if successful.
    """
    if (5 < len(block) < 3 or isinstance(block[0], dt.datetime)
            or any(isinstance(X, str) for X in block[1:])):
        return None
    if len(block) == 5:
        off, on = cast(dt.datetime, block[2]), cast(dt.datetime, block[3])
    else:
        off, on = cast(dt.datetime, block[-2]), cast(dt.datetime, block[-1])
    if off > on:
        off -= dt.timedelta(1)  # for dragover in first column
    return Sector(cast(str, block[0]), None, None, off, on, block)


def _columns_to_datastream(columns: tuple[Column, ...]) -> list[DataBlock]:
    """Process a tuple of columns into a stream of DataBlocks suitable for
    sector extraction.

    This function prepares the data for sector extraction by dealing with the
    anomalies caused by sectors and duties straddling midnight in a columnar
    presentation.

    If a sector straddles mignight, its data is found in two DataBlocks. The
    second DataBlock of a normal sector so split has the same form as a
    standby. The correct interpretation requires the context of the preceeding
    block. This is dealt with in the _extract_standard_sector function rather
    than here. What we can deal with is standby duties straddling midnight as
    they have a distinctive presentation where the first of the pair ends in a
    datetime and the second starts with a datetime. Thus if two datetimes
    touch, we can confidently combine the blocks at this stage.

    The problem is even more tricky for the first sector of the first column of
    the roster and the last sector of the last column. As far as possible this
    is fixed up in this function by adding fake data as required. This retains
    the maximum amount of data, and thus minimises any manual fix up that will
    need to be done by the user -- manual intervention is unavoidable since the
    data is simply unavailable.

    :param columns: A tuple of Column objects representing the roster.
    :return: A list of Datablocks suitable for sector extraction. Runs of
        strings (i.e. all day events etc.) are removed, standbys straddling
        midnight are joined, standbys straddling the first morning and the last
        evening of the roster are fixed up with fake data and a guard is added
        to the end so that if a normal sector straddled the last evening,
        normal processing will fix it up with fake data.
    """
    if not columns:
        return []
    fake_start_time = dt.datetime.combine(columns[0][0], dt.time())
    data: list[DataBlock] = [("???", fake_start_time)]
    for col in columns:
        for block in col[1]:
            # Drop runs of strings -- normally singleton all day events
            if all(isinstance(X, str) for X in block):
                continue
            # Join touching datetimes -- standby like straddling midnight
            if (isinstance(block[0], dt.datetime)
                    and isinstance(data[-1][-1], dt.datetime)):
                data[-1] = tuple(list(data[-1]) + list(block))
            else:
                data.append(block)
    fake_end_time = (dt.datetime.combine(columns[-1][0], dt.time())
                     + dt.timedelta(1))
    # Fix up standby straddling midnight in last column
    if len(data[-1]) == 2 and isinstance(data[-1][1], dt.datetime):
        data[-1] = tuple(list(data[-1]) + [fake_end_time])
    # set up end guard
    data.append(("???", fake_end_time, fake_end_time))
    # remove start guard if unused
    if data[0] == ("???", fake_start_time):
        del data[0]
    return data


def sectors(columns: tuple[Column, ...]) -> tuple[Sector, ...]:
    """Convert a tuple of DataBlocks into a tuple of Sectors"""
    data = _columns_to_datastream(columns)
    # extract standard sectors
    retval: list[Sector] = []
    processed = [False] * len(data)
    for c in range(len(data) - 1):
        if processed[c]:  # Skip over processed blocks
            continue
        sector, used = _extract_standard_sector(data[c], data[c + 1])
        if sector:
            for d in range(c, c + used):
                processed[d] = True
            retval.append(sector)
    # extract quasi sectors
    for c in range(len(data) - 1):
        if processed[c]:  # Skip over processed blocks
            continue
        sector = _extract_quasi_sector(data[c])
        if sector:
            processed[c] = True
            retval.append(sector)
    if not all(processed[:-1]):
        print("Warning: Some sectors could not be processed",
              file=sys.stderr)
    retval.sort(key=lambda x: x.off)
    return tuple(retval)


def duties(sectors: tuple[Sector, ...]) -> tuple[Duty, ...]:
    """Group sectors into duties.

    A sector is considered to be part of the same duty if the time elapsed
    since the on.chocks of the previous sector is 11 hours or greater. This
    accounts for two consecutive airport standbys (i.e. no pre/post duty time
    required) being separate duties with minumum rest between.

    :param sectors: The tuple of Sector objects to be grouped, sorted by off
        chocks time
    :return: A sorted tuple of Duty objects with the input Sectors grouped and
        duty start and finish times extracted.
    """
    assert all(isinstance(X, Sector) for X in sectors)
    assert tuple(sorted(sectors, key=lambda x: x.off)) == sectors
    groups: list[list[Sector]] = []
    last = dt.datetime.min
    for sector in sectors:
        if sector.off - last >= dt.timedelta(hours=11):
            groups.append([sector])
        else:
            groups[-1].append(sector)
        last = sector.on
    retval: list[Duty] = []
    for group in groups:
        retval.append(Duty(
            [X for X in group[0].src if isinstance(X, dt.datetime)][0],
            [X for X in group[-1].src if isinstance(X, dt.datetime)][-1],
            tuple(group)))
    return tuple(retval)


def _crew_strings(lines: tuple[Line, ...]) -> tuple[str, ...]:
    # find header of crew table
    for c, l in enumerate(lines):
        if not l:
            continue
        if re.match(r"DATE\s*RTES\s*NAMES", l[0]):
            break
    else:
        return tuple()  # crew table not found
    if len(lines) <= c + 1 or not lines[c + 1][0]:
        return tuple()  # protects against malformed file
    strings = lines[c + 1][0].replace(" ", " ").splitlines()
    out = ["", ]  # deal with strings going on to second line
    for s in strings:
        if not s:
            continue
        if s[0].isdigit():
            out.append(s)
        else:
            out[-1] += s
    return tuple(out[1:])


def crew_dict(lines: tuple[Line, ...]) -> CrewDict:
    """Extract crew lists from an AIMS detailed roster."""
    retval: CrewDict = {}
    for s in _crew_strings(lines):
        entries = re.split(r"\s*(\w{2})>\w* ", s)
        if len(entries) < 3:
            raise CrewFormatException
        try:
            datestr, route = entries[0].split()
            date = dt.datetime.strptime(datestr, "%d/%m/%Y").date()
        except ValueError:
            raise CrewFormatException
        crew: list[CrewMember] = []
        for name_string, role in zip(entries[2::2], entries[1::2]):
            name_string = " ".join([X.strip() for X in name_string.split()])
            crew.append(CrewMember(name_string, role))
        if route == "All":
            retval[(date, None)] = tuple(crew)
        else:
            for flight in route.split(","):
                retval[(date, flight)] = tuple(crew)
    return retval
