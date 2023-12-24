#!/usr/bin/python3
import re
import datetime as dt
from html.parser import HTMLParser
from typing import Union, NamedTuple
import enum
import itertools as it

import aims.aimstypes as T


class Break(enum.Enum):
    """Gaps between duties.

    A Break of type LINE indicates a gap between duties in a roster column.  A
    Break of type COLUMN indicates the gap between the end of one column and the
    start of the next.  A Break of type DUTY indicates a gap where rest is
    taken.
    """
    LINE = 0
    COLUMN = 1
    DUTY = 2
    SECTOR = 3


class DStr(NamedTuple):
    date: dt.date
    text: str


StreamItem = Union[DStr, Break, dt.datetime]
RosterStream = list[StreamItem]
DutyStream = list[StreamItem]
Column = list[str]
Line = list[str]


class DetailedRosterException(Exception):

    def __str__(self):
        return self.__doc__


class InputFileException(DetailedRosterException):
    "Input file does not appear to be an AIMS detailed roster."


class SectorFormatException(DetailedRosterException):
    "Sector with unexpected format found."


class CrewFormatException(DetailedRosterException):
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
        pass

    def handle_data(self, data):
        if self.in_td:
            self.output_list[-1][-1] += data


def lines(roster: str) -> list[Line]:
    """
    Turn an AIMS roster into a list of lines.

    Each line is represented by a list of cells.

    The input should be a string containing the HTML file of an AIMS detailed
    roster. The output has the form:

    [
        [ line0cell0, line0cell1, ..., line0cell31],
        [ line1cell0, line1cell1, ..., line1cell31],
        ...
        [ lineNcell0, lineNcell1, ..., lineNcell31]
    ]

    """
    parser = RosterParser()
    parser.feed(roster)
    if (len(parser.output_list) < 10
            or len(parser.output_list[1]) < 1
            or not parser.output_list[1][0].startswith("Personal")):
        raise InputFileException
    return parser.output_list


def extract_date(lines: list[list[str]]) -> dt.date:
    """
    Return the date as found in the Period: xx/xx/xxxx clause

    The input is 'lines' format as detailed in the lines() docstring. The output
    is a datetime.date object with the first day that the roster is applicable.
    """
    mo = re.search(r"Period: (\d{2}/\d{2}/\d{4})", lines[1][0])
    if not mo:
        raise InputFileException
    return dt.datetime.strptime(mo.group(1), "%d/%m/%Y").date()


def columns(lines: list[Line]) -> list[Column]:
    """
    Convert 'lines' format input to 'columns' format output.

    The input is 'lines' format as detailed in the lines() docstring. The output
    is a list of columns built from the rows with 32 cells that occur before the
    word Block is found in the row. It has the form:

    [
        [Col0Cell0, Col0Cell1, ...],
        [Col1Cell0, Col1Cell1, ...],
        ...
        [ColNCell0, ColNCell1, ...]
    ]
    """
    # assumption: main table starts on row 5 of the page 1 table
    width = len(lines[5])
    columns: list[list[str]] = [[] for _ in range(width)]
    for line in lines[5:]:
        if len(line) != width:
            continue
        if "Block" in line:
            break  # The last line contains the word "Block"
        for c, e in enumerate(line):
            columns[c].append(e.strip())
    return columns


def _process_column(col: list[str], date: dt.date):
    assert False not in [isinstance(X, str) for X in col[1:]]
    stream: list[StreamItem] = [Break.COLUMN]
    for entry in col[1:]:
        if entry == "":
            if not isinstance(stream[-1], Break):
                stream.append(Break.LINE)
        # bug workaround: roster uses non-existent time "24:00"
        elif entry == "24:00":
            stream.append(
                dt.datetime.combine(
                    date + dt.timedelta(days=1),
                    dt.time(0, 0)))
        else:
            try:  # try to treat entry like a time
                time = dt.datetime.strptime(entry, "%H:%M").time()
                stream.append(dt.datetime.combine(date, time))
            except ValueError:  # if that fails, treat it like a string
                stream.append(DStr(date, entry))
    # remove trailing break if there is one
    if isinstance(stream[-1], Break):
        del stream[-1]
    return stream[1:]


def _split_stream(stream, break_type):
    groups = it.groupby(stream, lambda x: x == break_type)
    return [list(X[1]) for X in it.islice(groups, 0, None, 2)]


def basic_stream(date: dt.date, columns: list[Column]) -> RosterStream:
    """Concatenates columns into a stream of datetime, DStr and Break objects

    :date: The date of the first column

    :columns: A list of Column structures. A Column is the list of strings
        extracted from the roster

    :returns: A list of datetime, DStr or Break objects. The stream returned
        from this function includes COLUMN and LINE breaks, but no DUTY breaks.
    """
    assert isinstance(date, dt.date) and isinstance(columns, (list, tuple))
    stream: RosterStream = [Break.COLUMN]
    for col in columns:
        assert isinstance(col, (list, tuple))
        if len(col) < 2:
            continue
        if col[0] == "":
            break  # column has no header means we're finished
        stream += _process_column(col, date)
        stream.append(Break.COLUMN)
        date += dt.timedelta(1)
    # there is a corner case where a sector finish time is dragged into the next
    # column by a duty time finishing after midnight, and another where a sector
    # time uses 24:00 as a start time but advances this to where 00:00 should
    # correctly sit. To counteract these cases, make sure datetimes in a
    # reversed stream only ever decrease.
    stream.reverse()
    for c, event in enumerate(stream):
        if isinstance(event, Break) and event == Break.COLUMN:
            last_datetime = dt.datetime(9999, 1, 1)
        elif isinstance(event, dt.datetime):
            if event > last_datetime:
                event -= dt.timedelta(days=1)
                stream[c] = event
            last_datetime = event
    stream.reverse()
    return stream


def _remove_singles(dstream: list[StreamItem]) -> list[StreamItem]:
    """Remove single DStr surrounded by Breaks"""
    keep_list = [True] * len(dstream)
    for c in range(1, len(dstream) - 1):
        if (isinstance(dstream[c], DStr)
                and isinstance(dstream[c - 1], Break)
                and isinstance(dstream[c + 1], Break)):
            keep_list[c] = False
            keep_list[c - 1] = False
    return list(it.compress(dstream, keep_list))


def _remove_intra_sector_column_breaks(
        dstream: list[StreamItem]
) -> list[StreamItem]:
    """Remove column breaks that are immediately followed by a dt.datetime"""
    keep_list = [True] * len(dstream)
    for c in range(1, len(dstream) - 1):
        if dstream[c] == Break.COLUMN and isinstance(
                dstream[c + 1], dt.datetime):
            keep_list[c] = False
    return list(it.compress(dstream, keep_list))


def _clean_sector_blocks(
        dstream: list[StreamItem]
) -> list[StreamItem]:
    """Clean up sector blocks, including column break removal"""
    keep = [True] * len(dstream)
    in_sector = False
    for c in range(1, len(dstream) - 1):
        if not keep[c]:
            continue
        if in_sector:
            if dstream[c] == Break.LINE:
                raise SectorFormatException
            if (isinstance(dstream[c], DStr)
                    and isinstance(dstream[c + 1], dt.datetime)):  # "to" found
                in_sector = False
                # remove any DStr up to next Break object
                i = c + 2
                while i < len(dstream) and not isinstance(dstream[i], Break):
                    if isinstance(dstream[i], DStr):
                        keep[i] = False
                    i += 1
            else:
                keep[c] = False  # remove column breaks and extra DStrs
        else:  # not in sector
            if isinstance(dstream[c], DStr):
                if isinstance(dstream[c - 1], dt.datetime):  # "from" found
                    in_sector = True
                elif isinstance(dstream[c - 1], DStr):
                    keep[c - 1] = False  # remove extra DStrs at start
    return list(it.compress(dstream, keep))


def duty_stream(bstream):
    """Processed an basic stream into a duty stream.

    :param bstream: A stream of datetime, DStr and Break objects, where
        the Break objects are either Break.LINE or Break.COLUMN

    :return: A duty stream: a stream of datetime, DStr and Break objects,
         where the Break objects are either Break.SECTOR or Break.DUTY
    """
    assert isinstance(bstream, (list, tuple))
    assert False not in [isinstance(X, (DStr, Break, dt.datetime))
                         for X in bstream]
    assert False not in [X in (Break.LINE, Break.COLUMN) for X in bstream
                         if isinstance(X, Break)]
    assert bstream[0] == Break.COLUMN and bstream[-1] == Break.COLUMN
    dstream = bstream[:]
    dstream = _remove_singles(dstream)
    dstream = _remove_intra_sector_column_breaks(dstream)
    dstream = _clean_sector_blocks(dstream)
    # remaining Break objects are either duty breaks if separated by more
    # than 8 hours, else they are sector breaks
    for c in range(1, len(dstream) - 2):
        if dstream[c] in (Break.LINE, Break.COLUMN):
            if (not isinstance(dstream[c - 1], dt.datetime)
                    or not isinstance(dstream[c + 2], dt.datetime)):
                raise SectorFormatException
            tdiff = (dstream[c + 2] - dstream[c - 1]).total_seconds()
            if tdiff >= 8 * 3600:
                dstream[c] = Break.DUTY
            else:
                dstream[c] = Break.SECTOR
    return dstream[1:-1]


def _duty(stream):
    """Converts a 'Duty stream' into a list of aimslib Duty objects'

    :param duty_stream: A stream of DStr, datetime and Break objects, with
        each stream representing one complete duty, i.e. all Break objects
        must be Break.SECTOR only.

    :returns: An aimslib Duty object
    """
    assert isinstance(stream, (list, tuple))
    assert False not in [type(X) in (DStr, dt.datetime, Break)
                         for X in stream]
    if len(stream) <= 1:
        return None  # empty stream or some sort of day off
    # the end of the last duty may not be included on the roster if it finishes
    # after midnight. For consistency, fake the end of this duty if necessary
    if (isinstance(stream[-1], DStr)
            and isinstance(stream[-2], dt.datetime)):
        faketime = dt.datetime.combine(
            stream[-2].date() + dt.timedelta(days=1),
            dt.time.min)
        stream = list(stream) + [
            DStr(faketime.date(), "???"), faketime, faketime]
    if not isinstance(stream[0], DStr):
        raise SectorFormatException
    tripid = (str((stream[0].date - dt.date(1980, 1, 1)).days), "")
    # split stream at sector breaks
    sector_streams = _split_stream(stream, Break.SECTOR)
    # duty times can now be extracted
    duty_start, duty_finish = _duty_times(sector_streams)
    # build sector list
    sectors = []
    for sector_stream in sector_streams:
        if not sector_stream or not isinstance(sector_stream[0], DStr):
            raise SectorFormatException
        # determine whether 'normal' sector by presence of DStr object
        for c, e in enumerate(sector_stream[1:-2]):
            if isinstance(e, DStr):
                sectors.append(_sector(sector_stream, c + 1))
                break
        else:  # no DStr objects found in expected range
            sectors.append(_quasi_sector(sector_stream))
    return T.Duty(tripid, duty_start, duty_finish, tuple(sectors))


def _duty_times(sectors):
    # duty times can be extracted from first and last sectors
    if not (isinstance(sectors[0][1], dt.datetime)
            and isinstance(sectors[-1][-1], dt.datetime)):
        raise SectorFormatException
    return (sectors[0][1], sectors[-1][-1])


def _sector(s, idx):
    # 'from' is at s[idx], thus s[idx + 1] should be 'to', s[idx - 1] should be
    # 'off blocks' and s[idx + 2] should be 'on blocks'
    if (idx == 1 or idx + 2 >= len(s)
            or not isinstance(s[idx + 1], DStr)
            or not isinstance(s[idx - 1], dt.datetime)
            or not isinstance(s[idx + 2], dt.datetime)):
        raise SectorFormatException
    flags = T.SectorFlags.NONE
    if s[idx].text[0] == "*":
        s[idx] = DStr(s[idx].date, s[idx].text[1:])
        flags |= T.SectorFlags.POSITIONING
    if s[0].text == "TAXI":
        flags |= T.SectorFlags.GROUND_DUTY
    return T.Sector(
        s[0].text, s[idx].text, s[idx + 1].text,
        s[idx - 1], s[idx + 2],
        s[idx - 1], s[idx + 2],
        None, None, flags,
        f"{s[0].date:%Y%m%d}{s[0].text}~")


def _quasi_sector(s):
    if False in [isinstance(X, dt.datetime) for X in s[1:]]:
        raise SectorFormatException
    name = s[0].text
    if len(s) < 3:
        raise SectorFormatException
    if len(s) == 5:
        start, finish = s[2], s[3]
    else:
        start, finish = s[1], s[-1]
    return T.Sector(
        name, None, None, start, finish, start, finish,
        None, None,
        T.SectorFlags.QUASI | T.SectorFlags.GROUND_DUTY,
        None)


def _crew_strings(roster: str) -> list[str]:
    lines_ = lines(roster)
    # find header of crew table
    for c, l in enumerate(lines_):
        if not l:
            continue
        if re.match(r"DATE\s*RTES\s*NAMES", l[0]):
            break
    else:
        return []  # crew table not found
    if len(lines_) <= c + 1 or not lines_[c + 1][0]:
        return []  # protects against malformed file
    return lines_[c + 1][0].replace(" ", " ").splitlines()


def _all_flights_mapping(duties: list[T.Duty]) -> dict[str, list[str]]:
    """Returns a mapping of the form {allkey: [crewlist_id1, ...], } where
    all_key has the form '%Y%m%dAll~' """
    sector_map: dict[str, list[str]] = {}
    for duty in duties:
        if not duty.sectors:
            continue
        key_all = f"{duty.start:%Y%m%d}All~"
        sector_map[key_all] = []
        for sector in duty.sectors:
            if not sector.crewlist_id:
                continue
            sector_map[key_all].append(sector.crewlist_id)
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
        roster: str,
        duties: list[T.Duty] = []
) -> dict[str, tuple[T.CrewMember, ...]]:
    """Extract crew lists from an AIMS detailed roster."""
    sector_map = _all_flights_mapping(duties)
    retval = {}
    for s in _fix_two_line_crews(_crew_strings(roster)):
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
            crew.append(T.CrewMember(name_string, role))
        if route == "All":
            key = f"{date:%Y%m%d}All~"
            for id_ in sector_map.get(key, []):
                retval[id_] = tuple(crew)
        else:
            for flight in route.split(","):
                key = f"{date:%Y%m%d}{flight}~"
                retval[key] = tuple(crew)
    return retval


def duties(s: str) -> list[T.Duty]:
    lines_ = lines(s)
    bstream = basic_stream(extract_date(lines_), columns(lines_))
    duty_streams = _split_stream(duty_stream(bstream), Break.DUTY)
    dutylist = []
    for stream in duty_streams:
        duty = _duty(stream)
        if duty:
            dutylist.append(duty)
    return dutylist
