import datetime as dt
import re
from typing import Optional

from bs4 import BeautifulSoup  # type: ignore

from aims.data_structures import Duty, Sector, CrewMember, AllDayEvent


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
    crew = (CrewMember(row[CP], "CP"), )
    return Sector(row[FLTNUM], row[REG], row[TYPE],
                  row[FROM], row[TO],
                  off, on,
                  False, False, crew)


def _duty(sectors: tuple[Sector, ...]) -> Duty:
    lowest_off = min([X.off for X in sectors])
    highest_on = max([X.on for X in sectors])
    return Duty(lowest_off - dt.timedelta(hours=1),
                highest_on + dt.timedelta(minutes=30),
                sectors)


def duties(html) -> tuple[tuple[Duty, ...], tuple[AllDayEvent, ...]]:
    soup = BeautifulSoup(html, "html5lib")
    sectors: list[Sector] = []
    re_date = re.compile(r"^\d{2}/\d{2}/\d{2}$")
    for row in soup.find_all("tr"):
        strings = tuple(Y[0].replace("\xa0", " ") if Y else "" for Y in
                        [tuple(X.stripped_strings) for X in row("td")])
        if (len(strings) > 10 and re_date.match(strings[DATE])):
            sector = _sector(strings)
            if sector:
                sectors.append(sector)
    groups = [[sectors[0]]]
    last_on = sectors[0].on
    for sector in sectors[1:]:
        if sector.off - last_on > dt.timedelta(hours=10):
            groups.append([sector])
        else:
            groups[-1].append(sector)
        last_on = sector.on
    return (tuple(_duty(tuple(X)) for X in groups), ())
