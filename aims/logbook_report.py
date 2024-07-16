#!/usr/bin/python3
import datetime as dt
from bs4 import BeautifulSoup  # type: ignore
import sys
import re

from aims.roster import Duty, Sector, CrewMember, InputFileException


DATE, FLTNUM, FROM, OFF, TO, ON, TYPE, REG, BLOCK, CP = range(0, 10)
STR_TABLE = tuple[tuple[str, ...], ...]


def parse(html: str) -> tuple[Duty, ...]:
    data = _extract(html)
    return _duties(data)


def _extract(html: str) -> STR_TABLE:
    # check it's an html5 file
    html5_header = "<!DOCTYPE html><html>"
    if html[:len(html5_header)] != html5_header:
        raise InputFileException
    soup = BeautifulSoup(html, "html5lib")
    rows = soup.find_all("tr")
    retval = []
    re_date = re.compile(r"^\d{2}/\d{2}/\d{2}$")
    for row in rows:
        row_data: list[str] = []
        for cell in row("td"):
            strings = list(cell.stripped_strings)
            if len(strings):
                row_data.append(strings[0])
        if (len(row_data) > 10 and row_data[DATE] and
                re_date.match(row_data[DATE])):
            retval.append(tuple(row_data))
    return tuple(retval)


def _sector(row: tuple[str, ...]) -> Sector:
    date = dt.datetime.strptime(row[DATE], "%d/%m/%y").date()
    off = dt.datetime.combine(
        date,
        dt.datetime.strptime(row[OFF], "%H:%M").time())
    on = dt.datetime.combine(
        date,
        dt.datetime.strptime(row[ON], "%H:%M").time())
    if on < off:
        on += dt.timedelta(1)
    return Sector(row[FLTNUM], row[REG], row[TYPE],
                  row[FROM], row[TO],
                  off, on,
                  False, False)


def _duty(
        sectors: tuple[Sector, ...],
        crew: dict[dt.datetime, str]
) -> Duty:
    lowest_off = min([X.off for X in sectors])
    highest_on = max([X.on for X in sectors])
    cpt_names = set([crew[X.off].replace("\xa0", " ") for X in sectors])
    return Duty(None,
                lowest_off - dt.timedelta(hours=1),
                highest_on + dt.timedelta(minutes=30),
                sectors, tuple(CrewMember(X, "CP") for X in cpt_names))


def _duties(data: STR_TABLE) -> tuple[Duty, ...]:
    sectors: list[Sector] = []
    crew: dict[dt.datetime, str] = {}
    for row in data:
        sector = _sector(row)
        sectors.append(sector)
        crew[sector.off] = row[CP]
    groups = [[sectors[0]]]
    last_on = sectors[0].on
    for sector in sectors[1:]:
        if sector.off - last_on > dt.timedelta(hours=10):
            groups.append([sector])
        else:
            groups[-1].append(sector)
        last_on = sector.on
    return tuple(_duty(tuple(X), crew) for X in groups)


if __name__ == "__main__":
    duties = parse(sys.stdin.read())
    for d in duties:
        print(d.start, d.finish, d.crew)
        for s in d.sectors:
            print("    ", s)
        print("----")
