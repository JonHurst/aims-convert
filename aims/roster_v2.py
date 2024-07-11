#!/usr/bin/python3
import datetime as dt
from typing import NamedTuple, Optional
from bs4 import BeautifulSoup
import pprint


class Sector(NamedTuple):
    name: str
    from_: Optional[str]
    to: Optional[str]
    off: dt.datetime
    on: dt.datetime


class Duty(NamedTuple):
    start: dt.datetime
    finish: dt.datetime
    sectors: tuple[Sector, ...]


class CrewMember(NamedTuple):
    name: str
    role: str


CrewList = tuple[CrewMember, ...]
CrewDict = dict[tuple[dt.date, Optional[str]], CrewList]

Data = tuple[str, ...]
Row = tuple[Data, ...]


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


def test():
    roster = open("/home/jon/downloads/ScheduleReport.html").read()
    pprint.pprint(extract(roster))


if __name__ == "__main__":
    test()
