#!/usr/bin/python3
import re
import datetime as dt
from html.parser import HTMLParser
from typing import Union, NamedTuple, Optional
import enum
import itertools as it
import requests


class CrewMember(NamedTuple):
    name: str
    role: str

    def __repr__(self):
        return f"CrewMember({self.name}, {self.role})"


class SectorFlags(enum.Flag):
    NONE = 0
    POSITIONING = enum.auto()
    GROUND_DUTY = enum.auto()
    QUASI = enum.auto()
    # QUASI means a standby or SEP segment recorded in a duty as a sector


class Sector(NamedTuple):
    name: str
    from_: Optional[str]
    to: Optional[str]
    off: dt.datetime
    on: dt.datetime
    reg: Optional[str]
    type_: Optional[str]
    flags: SectorFlags
    crewlist_id: str

    def __repr__(self):
        return (f"Sector('{self.name}', "
                f"'{self.from_}', '{self.to}', "
                f"{repr(self.off)}, {repr(self.on)}, "
                f"'{self.reg}', '{self.type_}', {repr(self.flags)}, "
                f"'{self.crewlist_id}')").replace("'None'", "None")


class Duty(NamedTuple):
    start: dt.datetime
    finish: dt.datetime
    sectors: Optional[list[Sector]]

    def __repr__(self):
        return (f"{repr(self.start)}, {repr(self.finish)}, "
                f"{self.sectors})")


class Break(enum.Enum):
    """Gaps between duties.

    A Break of type LINE indicates a gap between duties in a roster column. A
    Break of type COLUMN indicates the gap between the end of one column and
    the start of the next. A Break of type DUTY indicates a gap where rest is
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

    def handle_data(self, data):
        if self.in_td:
            self.output_list[-1][-1] += data


def lines(roster: str) -> list[Line]:
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
    return parser.output_list


def extract_date(lines: list[Line]) -> dt.date:
    """
    Return the date as found in the Period: xx/xx/xxxx clause on the first line
    of the roster.

    :param lines: A list of Line objects, as output by the lines function.
    :return: The full date of the first column of the main table of the roster.
    """
    mo = re.search(r"Period: (\d{2}/\d{2}/\d{4})", lines[1][0])
    if not mo:
        raise InputFileException
    return dt.datetime.strptime(mo.group(1), "%d/%m/%Y").date()


def columns(lines: list[Line]) -> list[Column]:
    """
    Extract the main table in the form of a list of Column objects. A Column
    object is a list of the strings, top to bottom, found in a single column of
    the main table of an AIMS roster.

    :param lines: An AIMS roster in the form output from the lines function.
    :return: A list of Column objects, one Column for each day.
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


def _process_column(col: Column, date: dt.date) -> list[StreamItem]:
    """
    Converts the strings found in a column into a list of StreamItems. Strings
    of the form HH:MM are converted to datetimes and runs of empty strings are
    each converted to a single LINE break. Everything else is converted to a
    DStr (dated string) by tagging it with the date.

    The "24:00" bug is also handled at this point by converting it to 00:00 on
    the following day.

    :param col: The Column to process.
    :param date: The date to apply to entries in the column

    :return: A list of StreamItems. Leading and trailing Breaks are removed.
    """
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


def _split_stream(stream, break_type) -> list[list[StreamItem]]:
    """
    Breaks up a stream of StreamItems into a list of substreams.

    :param stream: The stream of StreamItems to split
    :param break_type: The type of break to split the stream on
    :return: A list of streams. The breaks are not included.
    """
    groups = it.groupby(stream, lambda x: x == break_type)
    return [list(X[1]) for X in it.islice(groups, 0, None, 2)]


def basic_stream(date: dt.date, columns: list[Column]) -> list[StreamItem]:
    """Concatenates columns into a stream of datetime, DStr and Break objects

    :date: The date of the first column

    :columns: A list of Column structures. A Column is the list of strings
        extracted from the roster

    :returns: A list of datetime, DStr or Break objects. The stream returned
        from this function includes COLUMN and LINE breaks, but no DUTY breaks.
    """
    assert isinstance(date, dt.date) and isinstance(columns, (list, tuple))
    stream: list[StreamItem] = [Break.COLUMN]
    for col in columns:
        assert isinstance(col, (list, tuple))
        if len(col) < 2:
            continue
        if col[0] == "":
            break  # column has no header means we're finished
        stream += _process_column(col, date)
        stream.append(Break.COLUMN)
        date += dt.timedelta(1)
    # there is a corner case where a sector finish time is dragged into the
    # next column by a duty time finishing after midnight, and another where a
    # sector time uses 24:00 as a start time but advances this to where 00:00
    # should correctly sit. To counteract these cases, make sure datetimes in a
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


def _remove_single_dstrs(dstream: list[StreamItem]) -> list[StreamItem]:
    """
    Remove single DStr surrounded by Breaks. These DStrs will either be all day
    style duties such as days off or part time days, miscellaneous other
    strings such as SNCR, REST etc. or things like Ms to mark memos. These are
    impossible to reliably tell apart, so we just drop them.

    :param dstream: The list to process
    :return: The processed list
    """
    keep_list = [True] * len(dstream)
    for c in range(1, len(dstream) - 1):
        if (isinstance(dstream[c], DStr)
                and isinstance(dstream[c - 1], Break)
                and isinstance(dstream[c + 1], Break)):
            keep_list[c] = False
            keep_list[c - 1] = False
    return list(it.compress(dstream, keep_list))


def _remove_column_breaks_before_times(
        dstream: list[StreamItem]
) -> list[StreamItem]:
    """Remove column breaks that are immediately followed by a dt.datetime.
    This should only occur when a standby duty or something like an LPC
    straddles midnight.

    :param dstream: A list of StreamItems where any breaks are either
        Break.LINE or Break.COLUMN
    :return: A copy of the input list with any Break.COLUMN items occuring
        immediately before a datetime having been removed.
    """
    keep_list = [True] * len(dstream)
    for c in range(1, len(dstream) - 1):
        if dstream[c] == Break.COLUMN and isinstance(
                dstream[c + 1], dt.datetime):
            keep_list[c] = False
    return list(it.compress(dstream, keep_list))


def _clean_sector_blocks(
        dstream: list[StreamItem]
) -> list[StreamItem]:
    """Clean up sector blocks, including intra-sector column break removal.

    Sector blocks are often liberally sprinkled with extra information such as
    the type of aircraft assigned or various training codes. They may straddle
    midnight, and thus contain a column break. This algorithm first identifies
    the "from" cell as a DStr immediately preceded by a datetime. The sector
    identifier is then the nearest DStr above and the "to" cell is nearest DStr
    below that is immediately followed by a datetime. All other DStr and breaks
    within the sector block can be discarded.

    :param dstream: A list of StreamItems where the breaks are Break.Line or
        Break.Column.
    :return: A copy of the input stream with extraneous information removed
        from sector blocks.
    """
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


def _fix_edges(stream: list[StreamItem]) -> list[StreamItem]:
    """Fix cases where a duty straddles midnight at start or end of the roster
    by inserting fake data, possibly with a "???" marker.

    At the start of the roster, a single datetime followed by a break indicates
    that a standby-like duty has straddled midnight. A DStr followed by two
    datetimes may indicate that a sector is straddling midnight, but may also
    just be something like a standby. In the first case we insert the fake
    data, in the second we cannot tell what to do, so we just let it process as
    a standby would.

    At the end of the roster, we would normally expect two datetimes. If there
    is, instead, a DStr, we must have a sector straddling midnight since the
    input will already have any singleton DStrs stripped. If we have a datetime
    preceeded by a DStr be have a standby straddling midnight.

    :param list: A basic stream to be fixed. All single DStrs (i.e. DStrs
        surrounded by breaks) must have already been removed.
    :return: A copy of the input stream with the edges fixed as necessary

    """
    if len(stream) < 3:
        return stream
    fake_start: list[StreamItem] = []
    fake_end: list[StreamItem] = []
    if isinstance(stream[1], dt.datetime):
        if isinstance(stream[2], Break):
            d = stream[1].date()
            fake_start = [DStr(d, "???"), dt.datetime.combine(d, dt.time())]
        else:
            raise SectorFormatException
    if isinstance(stream[-2], DStr):
        d = stream[-2].date + dt.timedelta(1)
        fake_end = [DStr(d, "???"), dt.datetime.combine(d, dt.time())]
    elif (isinstance(stream[-2], dt.datetime)
          and isinstance(stream[-3], DStr)):
        d = stream[-2].date() + dt.timedelta(1)
        fake_end = [dt.datetime.combine(d, dt.time())]
    return ([Break.COLUMN] + fake_start + stream[1:-1]
            + fake_end + [Break.COLUMN])


def duty_stream(bstream):
    """Process a basic stream into a duty stream.

    A duty stream is a cleaned up basic stream with Break.LINE and Break.COLUMN
    objects removed or replaced with Break.SECTOR or Break.DUTY objects. The
    duty stream is a much more regular data structure than the basic stream,
    and should be clean enough to allow straightforward processing into lists
    of Duty objects.

    :param bstream: A stream of datetime, DStr and Break objects, where
        the Break objects are either Break.LINE or Break.COLUMN
    :return: A duty stream: a clean stream of datetime, DStr and Break objects,
         where the Break objects are either Break.SECTOR or Break.DUTY

    """
    assert isinstance(bstream, (list, tuple))
    assert False not in [isinstance(X, (DStr, Break, dt.datetime))
                         for X in bstream]
    assert False not in [X in (Break.LINE, Break.COLUMN) for X in bstream
                         if isinstance(X, Break)]
    assert bstream[0] == Break.COLUMN and bstream[-1] == Break.COLUMN
    if len(bstream) <= 2:
        return bsteam
    dstream = bstream[:]
    dstream = _remove_single_dstrs(dstream)
    dstream = _fix_edges(dstream)
    dstream = _remove_column_breaks_before_times(dstream)
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
    """Converts a stream representing a single duty into a Duty object

    :param stream: A list of StreamItems representing a single duty, i.e. the
        only Break objects must be Break.SECTOR.
    :returns: The Duty object
    """
    assert isinstance(stream, (list, tuple))
    assert False not in [type(X) in (DStr, dt.datetime, Break)
                         for X in stream]
    if len(stream) <= 1:
        return None  # empty stream or some sort of day off
    if not isinstance(stream[0], DStr):
        raise SectorFormatException
    sector_streams = _split_stream(stream, Break.SECTOR)
    duty_start, duty_finish = _duty_times(sector_streams)
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
    return Duty(duty_start, duty_finish, tuple(sectors))


def _duty_times(sectors: list[list[StreamItem]]
                ) -> tuple[dt.datetime, dt.datetime]:
    """Extract duty times from a list of sector streams

    :param sectors: A list of StreamItems lists, where each StreamItem list
        represents a single sector, i.e. it doesn't contain any Breaks.
   :return: A tuple pair, where the first item is the start time of the duty
        and the second is the end time of the duty.
    """
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
    flags = SectorFlags.NONE
    if s[idx].text[0] == "*":
        s[idx] = DStr(s[idx].date, s[idx].text[1:])
        flags |= SectorFlags.POSITIONING
    if s[0].text == "TAXI":
        flags |= SectorFlags.GROUND_DUTY
    return Sector(
        s[0].text, s[idx].text, s[idx + 1].text,
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
    return Sector(
        name, None, None, start, finish,
        None, None,
        SectorFlags.QUASI | SectorFlags.GROUND_DUTY,
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
        duties: list[Duty] = []
) -> dict[str, tuple[CrewMember, ...]]:
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


def _update_from_flightinfo(dutylist: list[Duty]) -> list[Duty]:
    retval: list[Duty] = []
    ids = []
    for duty in dutylist:
        if duty.sectors:
            ids.extend([f'{X.off:%Y%m%dT%H%M}F{X.name}'
                        for X in duty.sectors
                        if X.flags == SectorFlags.NONE])
    try:
        r = requests.post(
            "https://efwj6ola8d.execute-api.eu-west-1.amazonaws.com/"
            "default/reg",
            json={'flights': ids})
        r.raise_for_status()
        regntype_map = r.json()
    except requests.exceptions.RequestException:
        return dutylist  # if anything goes wrong, just return input
    for duty in dutylist:
        if not duty.sectors:
            continue
        updated_sectors: list[Sector] = []
        for sec in duty.sectors:
            flightid = f'{sec.off:%Y%m%dT%H%M}F{sec.name}'
            if flightid in regntype_map:
                reg, type_ = regntype_map[flightid]
                updated_sectors.append(sec._replace(reg=reg, type_=type_))
            else:
                updated_sectors.append(sec)
        retval.append(duty._replace(sectors=updated_sectors))
    return retval


def duties(s: str) -> list[Duty]:
    lines_ = lines(s)
    bstream = basic_stream(extract_date(lines_), columns(lines_))
    duty_streams = _split_stream(duty_stream(bstream), Break.DUTY)
    dutylist = []
    for stream in duty_streams:
        duty = _duty(stream)
        if duty:
            dutylist.append(duty)
    return _update_from_flightinfo(dutylist)
