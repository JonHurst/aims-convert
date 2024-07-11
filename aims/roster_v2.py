#!/usr/bin/python3
import datetime as dt
from typing import NamedTuple, Optional, TypeAlias
from bs4 import BeautifulSoup
import sys

DayEvent: TypeAlias = tuple[dt.date, str]


class Sector(NamedTuple):
    name: str
    from_: Optional[str]
    to: Optional[str]
    off: dt.datetime
    on: dt.datetime


class CrewMember(NamedTuple):
    name: str
    role: str


class Duty(NamedTuple):
    start: dt.datetime
    finish: dt.datetime
    sectors: tuple[Sector, ...]
    crew: tuple[CrewMember, ...]


Data = tuple[str, ...]
Row = tuple[Data, ...]

# column indices
DATE, CODES, DETAILS, DSTART, TIMES, DEND, BHR, DHR, IND, CREW = range(1, 11)


def extract(roster: str) -> tuple[Row, ...]:
    soup = BeautifulSoup(roster, "html5lib")
    retval = []
    for row in soup.find_all("tr"):
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


def all_day_events(data: tuple[Row, ...]) -> tuple[DayEvent, ...]:
    retval = []
    for row in data:
        if not row[TIMES]:
            retval.append((_convert_datestring(row[DATE][0]), row[CODES][0]))
    return tuple(retval)


def _extract_sectors(data: Row, date: dt.date) -> tuple[Sector, ...]:
    retval = []
    for c, code in enumerate(data[CODES]):
        name = code
        airports = data[DETAILS][c].split(" - ")
        times = data[TIMES][c].split("/")[0].split(" - ")
        if len(airports) == 2:
            retval.append(
                Sector(name, airports[0].strip(), airports[1].strip(),
                       _convert_timestring(times[0], date),
                       _convert_timestring(times[1], date)))
        else:
            retval.append(
                Sector(name, None, None,
                       _convert_timestring(times[0], date),
                       _convert_timestring(times[1], date)))
    return tuple(retval)


def duties(data: tuple[Row, ...]) -> tuple[Duty, ...]:
    retval = []
    for row in data:
        if not row[TIMES]:
            continue
        date = _convert_datestring(row[DATE][0])
        if row[DSTART]:
            start = _convert_timestring(row[DSTART][0], date)
            end = _convert_timestring(row[DEND][0], date)
        else:
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
        retval.append(Duty(start, end,
                           _extract_sectors(row, date),
                           tuple(crew)))
    return tuple(retval)


def test():
    roster = extract(sys.stdin.read())
    print("All Day Events\n==============")
    for e in all_day_events(roster):
        print(str(e[0]), e[1])
    print("\nDuties\n======")
    for d in duties(roster):
        print(d.start, d.finish)
        for c in d.crew:
            print("  ", c.role, ":", c.name)
        for s in d.sectors:
            print("  ", s.name, s.off, s.from_ or "", s.to or "", s.on)


if __name__ == "__main__":
    test()