#!/usr/bin/python3

from zoneinfo import ZoneInfo as Z
import io
import csv as libcsv
import datetime as dt
import re
import itertools

from aims.data_structures import Duty, Sector, CrewMember, AllDayEvent
import nightflight.night as nightcalc  # type: ignore
from nightflight.airport_nvecs import airfields as nvecs  # type: ignore

UTC = Z("UTC")
LT = Z("Europe/London")


def clean_name(name: str) -> str:
    parts = [X.strip().capitalize() for X in name.split()]
    for c, part in enumerate(parts):
        # remove bracketted stuff
        if part[0] == "(":
            parts[c] = ""
            continue
        # remove LR, SR, 50%
        if part.upper() in {"LR", "SR", "50%"}:
            parts[c] = ""
            continue
        # remove stars
        new = re.sub(r"\*+", "", part)
        # remove commas
        new = new.replace(",", "")
        # capitilize after - and '
        for char in ("-", "'"):
            index = new.find(char)
            if index not in {-1, len(new) - 1}:
                index += 1
                new = new[:index] + new[index:].capitalize()
        # capitilize after Mc
        index = new.find("Mc")
        if index == 0 and len(new) > 2:
            new = new[:2] + new[2:].capitalize()
        parts[c] = new
    return " ".join([X for X in parts if X])


def _night(sector: Sector) -> tuple[int, bool]:
    try:
        night_landing = nightcalc.night_p(nvecs[sector.to], sector.on)
        night_duration = nightcalc.night_duration(
            nvecs[sector.from_], nvecs[sector.to],
            sector.off, sector.on)
    except KeyError:
        return (0, False)
    return (round(night_duration), night_landing)


def _build_roster_string(start, end, block, string):
    start, end = [X.replace(tzinfo=UTC).astimezone(LT)
                  for X in (start, end)]
    duration = int((end - start).total_seconds()) // 60
    duration_str = f"{duration // 60}:{duration % 60:02d}"
    block_str = f"{block // 60}:{block % 60:02d}"
    return (f"{start:%d/%m/%Y %H:%M}-{end:%H:%M} "
            f"{string} {block_str}/{duration_str}")


def _roster_quasi(
        qsectors: tuple[Sector, ...],
        cursor: dt.datetime
) -> tuple[tuple[str, ...], dt.datetime]:
    retval: list[str] = []
    name = "Brief"
    for s in qsectors:
        if cursor < s.off:
            retval.append(_build_roster_string(cursor, s.off, 0, name))
            name = "Debrief"
        retval.append(_build_roster_string(s.off, s.on, 0, s.name))
        cursor = s.on
    return (tuple(retval), cursor)


def _roster_real(
        sectors: tuple[Sector, ...],
        cursor: dt.datetime
) -> tuple[str, dt.datetime]:
    assert sectors[0].from_
    airports: list[str] = [sectors[0].from_]
    block = 0
    start = cursor
    for sector in sectors:
        if sector.position:
            airports.append("[psn]")
        else:
            block += int((sector.on - sector.off).total_seconds()) // 60
        assert sector.to
        airports.append(sector.to)
    cursor = sectors[-1].on + dt.timedelta(minutes=30)
    return (
        _build_roster_string(start, cursor, block, '-'.join(airports)),
        cursor)


def roster(duties: tuple[Duty, ...]) -> str:
    output: list[str] = []
    for duty in duties:
        if not duty.finish:  # an all day duty
            continue
        cursor = duty.start
        for k, g in itertools.groupby(duty.sectors, key=lambda X: X.quasi):
            if k:  # group of quasi sectors
                new_output, cursor = _roster_quasi(tuple(g), cursor)
                output += new_output
            else:  # group of real sectors
                new, cursor = _roster_real(tuple(g), cursor)
                output.append(new)
        if cursor < duty.finish:
            output.append(
                _build_roster_string(cursor, duty.finish, 0, "Debrief"))
    return "\n".join(output)


def _efj_sector(sector: Sector) -> str:
    duration = (sector.on - sector.off).total_seconds() // 60
    night_duration, night_landing = _night(sector)
    night_flag = ""
    if night_duration == duration:
        night_flag = " n"
    elif night_duration:
        ldg_flag = " ln" if night_landing else ""
        night_flag = f" n:{night_duration}{ldg_flag}"
    return (f"{sector.from_}/{sector.to} "
            f"{sector.off:%H%M}/{sector.on:%H%M}{night_flag}")


def efj(duties: tuple[Duty, ...]) -> str:
    output = []
    for duty in duties:
        if not duty.finish:  # all day event
            continue
        output.append(f"{duty.start:%Y-%m-%d}")
        comment = ""
        if (len(duty.sectors) == 1 and duty.sectors[0].quasi):
            comment = f" #{duty.sectors[0].name}"
        output.append(f"{duty.start:%H%M}/{duty.finish:%H%M}{comment}")
        last_airframe = None
        last_crew = None
        for sector in duty.sectors:
            if sector.position or sector.quasi:
                continue
            if sector.crew:
                crew = [f"{X.role}:{clean_name(X.name)}" for X in sector.crew]
                if crew != last_crew:
                    output.append(f"{{ {', '.join(crew)} }}")
                last_crew = crew
            reg = sector.reg or "?-????"
            type_ = sector.type_ or "???"
            if last_airframe != (reg, type_):
                output.append(f"{reg}:{type_}")
                last_airframe = (reg, type_)
            output.append(_efj_sector(sector))
        output.append("")
    return "\n".join(output)


def csv(duties: tuple[Duty, ...]) -> str:
    output = io.StringIO(newline='')
    fieldnames = ['Off Blocks', 'On Blocks', 'Duration', 'Night', 'Origin',
                  'Destination', 'Registration', 'Type', 'Captain', 'Crew']
    writer = libcsv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction='ignore')
    writer.writeheader()
    for duty in duties:
        for sector in duty.sectors:
            if sector.position or sector.quasi:
                continue
            crew = [CrewMember(clean_name(X[0]), X[1]) for X in sector.crew]
            out_dict = {
                'Off Blocks': sector.off,
                'On Blocks': sector.on,
                'Duration':
                (sector.on - sector.off) // dt.timedelta(minutes=1),
                'Night': _night(sector)[0],
                'Origin': sector.from_,
                'Destination': sector.to
            }
            out_dict['Registration'] = sector.reg or ""
            out_dict['Type'] = sector.type_ or ""
            captains = [X.name for X in crew if X.role == "CP"]
            if not captains:
                out_dict['Captain'] = 'Self'
            else:
                out_dict['Captain'] = ', '.join(captains)
            out_dict['Crew'] = "; ".join(f"{X.role}:{X.name} " for X in crew)
            writer.writerow(out_dict)
    output.seek(0)
    return output.read()


vcalendar = """\
BEGIN:VCALENDAR\r
VERSION:2.0\r
PRODID:hursts.org.uk\r
{}\r
END:VCALENDAR\r
"""

vevent = """\
BEGIN:VEVENT\r
UID:{uid}\r
DTSTAMP:{modified}\r
DTSTART:{start}\r
DTEND:{end}\r
SUMMARY:{route}\r
{sectors}\
LAST-MODIFIED:{modified}\r
END:VEVENT"""

advevent = """\
BEGIN:VEVENT\r
UID:{uid}\r
DTSTAMP:{modified}\r
DTSTART;VALUE=DATE:{day:%Y%m%d}\r
SUMMARY:{ev}\r
TRANSP:TRANSPARENT\r
LAST-MODIFIED:{modified}\r
END:VEVENT"""

ical_datetime = "{:%Y%m%dT%H%M%SZ}"


def _build_dict(duty: Duty) -> dict[str, str]:
    event = {}
    event["start"] = ical_datetime.format(duty.start)
    event["end"] = ical_datetime.format(duty.finish)
    sector_strings = []
    airports = []
    from_ = None
    for sector in duty.sectors:
        if not from_ and sector.from_:
            from_ = sector.from_
        if sector.position:
            airports.append("[psn]")
        elif sector.quasi:
            if sector.from_:
                airports.append(f"[{sector.name}]")
            else:
                airports.append(sector.name)
        if sector.to:
            airports.append(sector.to)
        off, on = sector.off, sector.on
        from_to = ""
        if sector.from_ and sector.to:
            from_to = f" {sector.from_}/{sector.to} "
        airframe = ""
        if sector.reg and sector.type_:
            airframe = f" {sector.reg} {sector.type_}"
        sector_strings.append(
            f"{off:%H:%M}z-{on:%H:%M}z {sector.name}"
            f"{airframe}{from_to}")
    if from_:
        airports = [from_] + airports
    event["sectors"] = "DESCRIPTION:{}\r\n".format(
        "\\n\r\n ".join(sector_strings))
    event["uid"] = "{}{}@HURSTS.ORG.UK".format(
        duty.start.isoformat(), "".join(airports))
    event["route"] = "-".join(airports)
    event["modified"] = ical_datetime.format(dt.datetime.utcnow())
    return event


def ical(duties: tuple[Duty, ...], ade: tuple[AllDayEvent, ...]) -> str:
    events = []
    for duty in duties:
        d = _build_dict(duty)
        events.append(vevent.format(**d))
    for e in ade:
        uid = "{}{}@HURSTS.ORG.UK".format(
            e.date.isoformat(), e.code)
        modified = ical_datetime.format(dt.datetime.utcnow())
        events.append(advevent.format(
                day=e.date,
                ev=e.code,
                modified=modified,
                uid=uid))
    return vcalendar.format("\r\n".join(events))
