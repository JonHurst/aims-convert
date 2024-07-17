#!/usr/bin/python3
import datetime as dt
from bs4 import BeautifulSoup  # type: ignore
import sys
import re
from typing import Optional

from aims.data_structures import Duty, Sector, CrewMember


DATE, FLTNUM, FROM, OFF, TO, ON, TYPE, REG, BLOCK, CP = range(1, 11)


def _sector(row: tuple[str, ...]) -> Optional[Sector]:
    if not row[FLTNUM]:  # this is a sim sector
        return None
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
                sectors,
                tuple(CrewMember(X, "CP") for X in sorted(cpt_names) if X))


def duties(soup) -> tuple[Duty, ...]:
    sectors: list[Sector] = []
    crew: dict[dt.datetime, str] = {}
    re_date = re.compile(r"^\d{2}/\d{2}/\d{2}$")
    for row in soup.find_all("tr"):
        strings = tuple(Y[0].replace("\xa0", " ") if Y else "" for Y in
                        [tuple(X.stripped_strings) for X in row("td")])
        if (len(strings) > 10 and re_date.match(strings[DATE])):
            sector = _sector(strings)
            if sector:
                sectors.append(sector)
                crew[sector.off] = strings[CP]
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
    soup = BeautifulSoup(sys.stdin.read(), "html5lib")
    for d in duties(soup):
        print(d.start, d.finish, d.crew)
        for s in d.sectors:
            print("    ", s)
        print("----")
