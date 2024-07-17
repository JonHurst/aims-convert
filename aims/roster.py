#!/usr/bin/python3
import datetime as dt
from bs4 import BeautifulSoup  # type: ignore
import sys

from aims.data_structures import Duty, Sector, CrewMember, InputFileException


Row = tuple[tuple[str, ...], ...]

# column indices
DATE, CODES, DETAILS, DSTART, TIMES, DEND, BHR, DHR, IND, CREW = range(1, 11)


def _convert_datestring(in_: str) -> dt.date:
    try:
        return dt.datetime.strptime(in_.split()[0], "%d/%m/%Y").date()
    except ValueError:
        raise InputFileException


def _convert_timestring(in_: str, date: dt.date) -> dt.datetime:
    try:
        if in_[-2:] == "⁺¹":
            in_ = in_[:-2]
            date = date + dt.timedelta(1)
        time = dt.datetime.strptime(in_.replace("A", ""), "%H:%M").time()
        return dt.datetime.combine(date, time)
    except ValueError:
        raise InputFileException


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


def _duty(row: Row) -> Duty:
    if len(row) != 12:
        raise InputFileException
    date = _convert_datestring(row[DATE][0])
    # if there are no times, it is an all day event
    if not row[TIMES]:
        return Duty(row[CODES][0],
                    dt.datetime.combine(date, dt.time()),
                    None, (), ())
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
    return Duty(None, start, end,
                _sectors(row, date),
                tuple(crew))


def duties(soup) -> tuple[Duty, ...]:
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
            retval.append(_duty(strings))
    except (StopIteration, IndexError):
        raise InputFileException
    return tuple(retval)


def test():
    soup = BeautifulSoup(sys.stdin.read(), "html5lib")
    for d in duties(soup):
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
