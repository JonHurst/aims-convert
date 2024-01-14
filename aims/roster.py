#!/usr/bin/python3
import re
import datetime as dt
from html.parser import HTMLParser
from typing import Union, NamedTuple, Optional, cast
import itertools as it


class Sector(NamedTuple):
    name: str
    from_: Optional[str]
    to: Optional[str]
    off: dt.datetime
    on: dt.datetime
    all_times: tuple[dt.datetime, ...]


class Duty(NamedTuple):
    start: dt.datetime
    finish: dt.datetime
    sectors: tuple[Sector, ...]


class CrewMember(NamedTuple):
    name: str
    role: str


Datum = Union[str, dt.datetime]
DataBlock = tuple[Datum, ...]
Column = tuple[dt.date, tuple[DataBlock, ...]]
Line = tuple[str, ...]


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
    """
    Turn an AIMS roster into a list of Line objects.

    An AIMS roster is fundamentally a very complex HTML table. Each Line object
    represents a row of that table, and each string contained in the Line
    object represents the contents of a cell.

    :param roster: A string containing the HTML of an AIMS detailed roster.
    :return: A list of Line objects representing the text of the roster.
    """
    parser = RosterParser()
    parser.feed(roster)
    if (len(parser.output_list) < 10
            or len(parser.output_list[1]) < 1
            or not parser.output_list[1][0].startswith("Personal")):
        raise InputFileException
    return tuple(cast(Line, tuple(X)) for X in parser.output_list)


def columns(lines: tuple[Line, ...]) -> tuple[Column, ...]:
    """
    Extract the main table in the form of a list of Column objects.

    :param lines: An AIMS roster in the form output from the lines function.
    :return: A list of Column objects, one Column for each day. A Column object
        is a tuple consisting of a datetime in the first field and a tuple of
        DataBlock objects in the second field.
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
    groups = [list(X[1]) for X in it.islice(it.groupby(converted, bool), 0,
                                            None, 2)]
    return tuple(cast(DataBlock, tuple(X)) for X in groups)


def _extract_standard_sector(
        block: DataBlock, extra_block: DataBlock
) -> tuple[Optional[Sector], int]:
    all_times = [cast(dt.datetime, X)
                 for X in block if isinstance(X, dt.datetime)]
    id_, off, from_, to, on, used = None, None, None, None, None, 0
    try:
        idx = 2
        # find from
        while not (isinstance(block[idx], str)
                   and isinstance(block[idx - 1], dt.datetime)):
            idx += 1
        off = cast(dt.datetime, block[idx - 1])
        from_ = cast(str, block[idx])
        # find id
        backtrack = idx - 2
        while not (isinstance(block[backtrack], str)):
            backtrack -= 1
        id_ = cast(str, block[backtrack])
        # find to
        idx += 1
        while not (isinstance(block[idx], str)
                   and isinstance(block[idx + 1], dt.datetime)):
            idx += 1
        to = cast(str, block[idx])
        on = cast(dt.datetime, block[idx + 1])
        used = 1
    except IndexError:
        if not id_:
            return (None, 0)
        # If we get here, we got as far as finding an id but ran out of block
        # before finding a to and on. Try to extract them from the extra block.
        all_times.extend([cast(dt.datetime, X)
                          for X in extra_block if isinstance(X, dt.datetime)])

        try:
            idx = 0
            while not (isinstance(extra_block[idx], str)
                       and isinstance(extra_block[idx + 1], dt.datetime)):
                idx += 1
            to = cast(str, extra_block[idx])
            on = cast(dt.datetime, extra_block[idx + 1])
            used = 2
        except IndexError:
            return (None, 0)
    # fix for dragover case -- reduce sectors over 24 hours by 24 hours
    if on - cast(dt.datetime, off) > dt.timedelta(1):
        idx = all_times.index(on)
        on -= dt.timedelta(1)
        all_times[idx] = on
    return (Sector(id_, from_, to, cast(dt.datetime, off),
                   on, tuple(all_times)), used)


def _extract_quasi_sector(tblock: DataBlock) -> tuple[Sector, int]:
    block = list(tblock)
    if (all(isinstance(X, dt.datetime) for X in block[1:])
            and isinstance(block[0], str)):
        if len(block) == 5:
            off, on = cast(dt.datetime, block[2]), cast(dt.datetime, block[3])
        else:
            off, on = cast(dt.datetime, block[1]), cast(dt.datetime, block[-1])
        all_times = [cast(dt.datetime, X) for X in block
                     if isinstance(X, dt.datetime)]
        return (Sector(cast(str, block[0]), None, None, off, on,
                       tuple(all_times)), 1)
    else:
        raise SectorFormatException


def _columns_to_datastream(columns: tuple[Column, ...]) -> list[DataBlock]:
    data: list[DataBlock] = []
    for col in columns:
        for block in col[1]:
            if len(block) == 1 and isinstance(block[0], str):
                continue
            if isinstance(block[0], dt.datetime):
                data[-1] = tuple(list(data[-1]) + list(block))
            else:
                data.append(block)
    # set up end guards
    fake_end_date = (dt.datetime.combine(columns[-1][0], dt.time())
                     + dt.timedelta(1))
    if isinstance(data[-1][-1], dt.datetime):
        data.append((fake_end_date, fake_end_date))
    else:
        data.append(("???", fake_end_date, fake_end_date))
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
        for d in range(c, c + used):
            processed[d] = True
        if used:
            retval.append(cast(Sector, sector))
    # extract quasi sectors
    for c in range(len(data) - 1):
        if processed[c]:  # Skip over processed blocks
            continue
        sector, used = _extract_quasi_sector(data[c])
        if used:
            processed[c] = True
            retval.append(cast(Sector, sector))
    return tuple(retval)


def _crew_strings(lines: list[Line]) -> list[str]:
    # find header of crew table
    for c, l in enumerate(lines):
        if not l:
            continue
        if re.match(r"DATE\s*RTES\s*NAMES", l[0]):
            break
    else:
        return []  # crew table not found
    if len(lines) <= c + 1 or not lines[c + 1][0]:
        return []  # protects against malformed file
    return lines[c + 1][0].replace(" ", " ").splitlines()


def _all_flights_mapping(duties: list[Duty]) -> dict[str, list[str]]:
    """Returns a mapping of the form {allkey: [crewlist_id1, ...], } where
    all_key has the form '%Y%m%dAll~' """
    sector_map: dict[str, list[str]] = {}
    for duty in duties:
        if not duty.sectors:
            continue
        key_all = f"{duty.start:%Y%m%d}All~"
        sector_map[key_all] = []
        for sector in duty.sectors:
            sector_map[key_all].append(f"{sector.off:%Y%m%d}{sector.name}~")
    return sector_map


def _fix_two_line_crews(crew_strings):
    """Return a list of strings where two line crew strings are joined"""
    # Very occasionally there are so many crew that a crew member drops
    # onto a second line. Normal lines start with dates, so if there is no
    # digit at the start of the string, concatenate it to the previous one.
    out = ["", ]
    for s in crew_strings:
        if not s:
            continue
        if s[0].isdigit():
            out.append(s)
        else:
            out[-1] += s
    return out[1:]


def crew(
        lines: list[Line],
        duties: list[Duty] = []
) -> dict[str, tuple[CrewMember, ...]]:
    """Extract crew lists from an AIMS detailed roster."""
    sector_map = _all_flights_mapping(duties)
    retval = {}
    for s in _fix_two_line_crews(_crew_strings(lines)):
        entries = re.split(r"\s*(\w{2})>\w* ", s)
        if len(entries) < 3:
            raise CrewFormatException
        try:
            datestr, route = entries[0].split()
            date = dt.datetime.strptime(datestr, "%d/%m/%Y").date()
        except ValueError:
            raise CrewFormatException
        crew = []
        for name_string, role in zip(entries[2::2], entries[1::2]):
            name_string = " ".join([X.strip() for X in name_string.split()])
            crew.append(CrewMember(name_string, role))
        if route == "All":
            key = f"{date:%Y%m%d}All~"
            for id_ in sector_map.get(key, []):
                retval[id_] = tuple(crew)
        else:
            for flight in route.split(","):
                key = f"{date:%Y%m%d}{flight}~"
                retval[key] = tuple(crew)
    return retval


def duties(tsectors) -> list[Duty]:
    if not tsectors:
        return []
    sectors = list(tsectors)
    sectors.sort(key=lambda x: x.off)
    tags, last = [0], sectors[0].off
    last = sectors[0].on
    for sector in sectors[1:]:
        if sector.off - last < dt.timedelta(hours=8):
            tags.append(tags[-1])
        else:
            tags.append(tags[-1] + 1)
        last = sector.on
    tag_it = iter(tags)
    retval: list[Duty] = []
    for group in it.groupby(sectors, lambda x: next(tag_it)):
        sector_group = list(group[1])
        retval.append(Duty(
            min(sector_group[0].all_times),
            max(sector_group[-1].all_times),
            tuple(sector_group)))
    return retval
