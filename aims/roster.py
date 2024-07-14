#!/usr/bin/python3
import datetime as dt
from typing import NamedTuple, Optional
from bs4 import BeautifulSoup  # type: ignore
import sys


class Sector(NamedTuple):
    name: str
    reg: Optional[str]
    type_: Optional[str]
    from_: Optional[str]
    to: Optional[str]
    off: dt.datetime
    on: dt.datetime
    quasi: bool
    position: bool


class CrewMember(NamedTuple):
    name: str
    role: str


class Duty(NamedTuple):
    code: Optional[str]  # only all day event has code
    start: dt.datetime
    finish: Optional[dt.datetime]  # all day event has None
    sectors: tuple[Sector, ...]
    crew: tuple[CrewMember, ...]


Data = tuple[str, ...]
Row = tuple[Data, ...]

# column indices
DATE, CODES, DETAILS, DSTART, TIMES, DEND, BHR, DHR, IND, CREW = range(1, 11)


class RosterException(Exception):

    def __str__(self):
        return self.__doc__


class InputFileException(RosterException):
    "Input file does not appear to be an AIMS roster."


def _extract(roster: str) -> tuple[Row, ...]:
    # check it's an html5 file
    html5_header = "<!DOCTYPE html><html>"
    if roster[:len(html5_header)] != html5_header:
        raise InputFileException
    # make some soup
    soup = BeautifulSoup(roster, "html5lib")
    # check it's a Personal Crew Schedule Report
    rows = soup.find_all("tr")
    if (not rows or len(rows) < 2 or
            next(rows[1].stripped_strings) != "Personal Crew Schedule Report"):
        raise InputFileException
    # process the roster
    retval = []
    for row in rows:
        row_data = []
        for entry in row("td"):
            row_data.append(tuple([X.replace("\xa0", " ")
                                   for X in entry.stripped_strings]))
        retval.append(tuple(row_data))
    # find start of table
    table_start = None
    for c, row in enumerate(retval):
        if len(row) > 1 and len(row[1]) and row[1][0] == "Schedule Details":
            table_start = c + 2
            break
    # find end of table
    table_end = None
    for c, row in enumerate(retval):
        if (len(row) > 2 and len(row[2]) and
                row[2][0] == "Total Hours and Statistics"):
            table_end = c - 1
            break
    return tuple(retval[table_start:table_end])


def _convert_datestring(in_: str) -> dt.date:
    return dt.datetime.strptime(in_.split()[0], "%d/%m/%Y").date()


def _convert_timestring(in_: str, date: dt.date) -> dt.datetime:
    if in_[-2:] == "⁺¹":
        in_ = in_[:-2]
        date = date + dt.timedelta(1)
    time = dt.datetime.strptime(in_.replace("A", ""), "%H:%M").time()
    return dt.datetime.combine(date, time)


def _extract_sectors(data: Row, date: dt.date) -> tuple[Sector, ...]:
    retval = []
    for c, code in enumerate(data[CODES]):
        code_split = code.split()
        name = code_split[0]
        type_ = None
        if len(code_split) == 2 and code_split[1][0] == "[":
            type_ = code_split[1][1:-1]
        airports = [X.strip() for X in data[DETAILS][c].split(" - ")]
        times = data[TIMES][c].split("/")[0].split(" - ")
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
                       quasi, position))
        else:
            retval.append(
                Sector(name, None, None, None, None,
                       _convert_timestring(times[0], date),
                       _convert_timestring(times[1], date),
                       True, False))
    return tuple(retval)


def parse(html: str) -> tuple[Duty, ...]:
    data = _extract(html)
    # import pprint
    # pprint.pprint(data)
    return _duties(data)


def _duties(data: tuple[Row, ...]) -> tuple[Duty, ...]:
    retval = []
    for row in data:
        date = _convert_datestring(row[DATE][0])
        # if there are no times, it is an all day event
        if not row[TIMES]:
            retval.append(
                Duty(row[CODES][0],
                     dt.datetime.combine(date, dt.time()),
                     None, (), ()))
            continue
        # If there duty start/finish does not exist, take the times from
        # the only sector. Details will be recorded in Duty.sectors.
        if row[DSTART]:
            start = _convert_timestring(row[DSTART][0], date)
            end = _convert_timestring(row[DEND][0], date)
        else:
            assert len(row[TIMES]) == 1
            times = row[TIMES][0].split(" - ")
            start = _convert_timestring(times[0], date)
            end = _convert_timestring(times[1], date)
        crew = []
        for m in row[CREW]:
            strings = m.split(" - ")
            if len(strings) >= 3:
                if strings[1] == "PAX":
                    continue
                crew.append(CrewMember(strings[-1], strings[0]))
            else:
                crew[-1] = CrewMember(crew[-1].name + " " + strings[0],
                                      crew[-1].role)
        retval.append(Duty(None, start, end,
                           _extract_sectors(row, date),
                           tuple(crew)))
    return tuple(retval)


def test():
    for d in parse(sys.stdin.read()):
        if not d.finish:
            print("ADE: ", d.start, d.code)
            continue
        print("DUTY: ", d.start, d.finish)
        for c in d.crew:
            print("  ", c.role, ":", c.name)
        for s in d.sectors:
            print("  ", s.name, s.off, s.from_ or "", s.to or "", s.on,
                  "Q" if s.quasi else "", "P" if s.position else "")


if __name__ == "__main__":
    test()
