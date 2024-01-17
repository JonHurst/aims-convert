#!/usr/bin/python3

from typing import Dict
from zoneinfo import ZoneInfo as Z
import io
import csv as libcsv
import datetime as dt
import re

from aims.roster import Duty, Sector, CrewDict, DayEvent
import nightflight.night as nightcalc  # type: ignore
from nightflight.airport_nvecs import airfields as nvecs  # type: ignore
from aims.airframe_lookup import airframes, sector_id


def clean(name: str) -> str:
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


def _night(sector: Sector) -> float:
    try:
        night_duration = nightcalc.night_duration(
            nvecs[sector.from_], nvecs[sector.to],
            sector.off, sector.on)
    except KeyError:
        return 0.0
    duration = (sector.on - sector.off).total_seconds() / 60
    return round(night_duration / duration, 3)


def roster(duties: tuple[Duty, ...]) -> str:
    UTC = Z("UTC")
    LT = Z("Europe/London")
    output = []
    for duty in duties:
        if not duty.sectors:
            continue
        start, end = [X.replace(tzinfo=UTC).astimezone(LT)
                      for X in (duty.start, duty.finish)]
        duration = int((end - start).total_seconds()) // 60
        from_ = None
        airports = []
        block = 0
        for sector in duty.sectors:
            if not from_ and sector.from_:
                from_ = sector.from_.strip("*")
            if sector.from_ and sector.from_[0] == "*":
                airports.append("[psn]")
            if sector.to:
                airports.append(sector.to)
                off, on = sector.off, sector.on
                block += int((on - off).total_seconds()) // 60
            else:
                airports.append(sector.name)
        if from_:
            airports = [from_] + airports
        duration_str = f"{duration // 60}:{duration % 60:02d}"
        block_str = f"{block // 60}:{block % 60:02d}"
        output.append(f"{start:%d/%m/%Y %H:%M}-{end:%H:%M} "
                      f"{'-'.join(airports)} {block_str}/{duration_str}")
    return "\n".join(output)


def freeform(
        duties: tuple[Duty, ...],
        crewdict: CrewDict
) -> str:
    output = []
    regntype = airframes(duties)
    for duty in duties:
        if not duty.sectors:
            continue
        output.append(f"{duty.start:%Y-%m-%d}")
        comment = ""
        if (len(duty.sectors) == 1 and not duty.sectors[0].from_):
            comment = f" #{duty.sectors[0].name}"
        output.append(f"{duty.start:%H%M}/{duty.finish:%H%M}{comment}")
        last_crew, last_reg = None, None
        duty_crew = list(crewdict.get((duty.start.date(), None), []))
        for sector in duty.sectors:
            if not sector.from_ or sector.from_[0] == "*":
                continue
            sector_crew = list(crewdict.get(
                (sector.off.date(), sector.name), []))
            crew = [f"{X.role}:{clean(X.name)}"
                    for X in duty_crew + sector_crew]
            if crew != last_crew:
                output.append(f"{{ {', '.join(crew)} }}")
                last_crew = crew
            reg, type_ = regntype.get(sector_id(sector), (None, None))
            if reg and type_ and reg != last_reg:
                output.append(f"{reg}:{type_}")
                last_reg = reg
            # sector
            night_frac = _night(sector)
            night_str = f" { night_frac:0.3}" if night_frac else ""
            output.append(
                f"{sector.from_}/{sector.to} "
                f"{sector.off:%H%M}/{sector.on:%H%M}{night_str}")
        output.append("")
    return "\n".join(output)


def csv(
        duties: tuple[Duty, ...],
        crewdict: CrewDict,
        fo: bool
) -> str:
    regntype = airframes(duties)
    output = io.StringIO(newline='')
    fieldnames = ['Off Blocks', 'On Blocks', 'Origin', 'Destination',
                  'Registration', 'Type', 'Captain', 'Role', 'Crew', 'Night']
    fieldname_map = (('Off Blocks', 'off'), ('On Blocks', 'on'),
                     ('Origin', 'from_'), ('Destination', 'to'))
    writer = libcsv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction='ignore',
        dialect='unix')
    writer.writeheader()
    for duty in duties:
        if not duty.sectors:
            continue
        duty_crew = list(crewdict.get((duty.start.date(), None), []))
        for sector in duty.sectors:
            if not sector.from_:
                continue
            sector_crew = list(crewdict.get(
                (sector.off.date(), sector.name), []))
            sec_dict = sector._asdict()
            for fn, sfn in fieldname_map:
                sec_dict[fn] = sec_dict[sfn]
            sec_dict['Role'] = 'p1s' if fo else 'p1'
            crewlist = duty_crew + sector_crew
            sec_dict['Captain'] = 'Self'
            reg, type_ = regntype.get(sector_id(sector), ("", ""))
            sec_dict['Registration'] = reg
            sec_dict['Type'] = type_
            if fo and crewlist and crewlist[0].role == 'CP':
                sec_dict['Captain'] = crewlist[0].name
            crewstr = "; ".join([f"{X[1]}:{clean(X[0])}" for X in crewlist])
            sec_dict['Crew'] = crewstr
            sec_dict['Night'] = _night(sector)
            writer.writerow(sec_dict)

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


def _build_dict(duty: Duty, regntype) -> Dict[str, str]:
    event = {}
    event["start"] = ical_datetime.format(duty.start)
    event["end"] = ical_datetime.format(duty.finish)
    sector_strings = []
    airports = []
    from_ = None
    if duty.sectors:
        for sector in duty.sectors:
            if not from_ and sector.from_:
                from_ = sector.from_
            if not sector.to:
                airports.append(sector.name)
            elif sector.from_ and sector.from_[0] == "*":
                airports.append("[psn]")
            if sector.to:
                airports.append(sector.to)
            off, on = sector.off, sector.on
            from_to = ""
            reg, type_ = regntype.get(sector_id(sector), ("", ""))
            type_ = ":" + type_ if type_ else ""
            if sector.from_ and sector.to:
                from_to = f"{sector.from_}/{sector.to} "
            sector_strings.append(
                f"{off:%H:%M}z-{on:%H:%M}z {sector.name} "
                f"{from_to}"
                f"{reg}{type_}")
    if from_:
        airports = [from_] + airports
    event["sectors"] = "DESCRIPTION:{}\r\n".format(
        "\\n\r\n ".join(sector_strings))
    event["uid"] = "{}{}@HURSTS.ORG.UK".format(
        duty.start.isoformat(), "".join(airports))
    event["route"] = "-".join(airports)
    event["modified"] = ical_datetime.format(dt.datetime.utcnow())
    return event


def ical(duties: tuple[Duty, ...], all_day_events: tuple[DayEvent, ...]
         ) -> str:
    events = []
    regntype = airframes(duties)
    for duty in duties:
        d = _build_dict(duty, regntype)
        events.append(vevent.format(**d))
    for ade in all_day_events:
        uid = "{}{}@HURSTS.ORG.UK".format(
            ade[0].isoformat(), ade[1])
        modified = ical_datetime.format(dt.datetime.utcnow())
        events.append(advevent.format(
            day=ade[0],
            ev=ade[1],
            modified=modified,
            uid=uid
        ))
    return vcalendar.format("\r\n".join(events))
