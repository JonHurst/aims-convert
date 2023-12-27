#!/usr/bin/python3

from typing import List, Dict
from zoneinfo import ZoneInfo as Z
import io
import csv as libcsv
import datetime as dt

from aims.roster import Duty, SectorFlags, CrewMember
from aims.name_cleanup import clean
import nightflight.night as nightcalc  # type: ignore
from nightflight.airport_nvecs import airfields as nvecs  # type: ignore


def roster(duties: List[Duty]) -> str:
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
                from_ = sector.from_
            if sector.flags & SectorFlags.QUASI:
                airports.append(sector.name)
            elif sector.flags & SectorFlags.POSITIONING:
                airports.append("[psn]")
            else:
                off, on = sector.sched_start, sector.sched_finish
                block += int((on - off).total_seconds()) // 60
            if sector.to:
                airports.append(sector.to)
        if from_:
            airports = [from_] + airports
        duration_str = f"{duration // 60}:{duration % 60:02d}"
        block_str = f"{block // 60}:{block % 60:02d}"
        output.append(f"{start:%d/%m/%Y %H:%M}-{end:%H:%M} "
                      f"{'-'.join(airports)} {block_str}/{duration_str}")
    return "\n".join(output)


def freeform(
        duties: List[Duty],
        crews: Dict[str, tuple[CrewMember, ...]]
) -> str:
    output = []
    for duty in duties:
        if not duty.sectors:
            continue
        output.append(f"{duty.start:%Y-%m-%d}")
        comment = ""
        if (len(duty.sectors) == 1
                and (duty.sectors[0].flags & SectorFlags.QUASI)):
            comment = f" #{duty.sectors[0].name}"
        output.append(f"{duty.start:%H%M}/{duty.finish:%H%M}{comment}")
        last_crew, last_reg = None, None
        for sector in duty.sectors:
            if not sector.act_start or sector.flags != SectorFlags.NONE:
                continue

            # crewlist
            if sector.crewlist_id and sector.crewlist_id in crews:
                crew = [f"{X[1]}:{clean(X[0])}"
                        for X in crews[sector.crewlist_id]]
                if crew != last_crew:
                    output.append(f"{{ {', '.join(crew)} }}")
                    last_crew = crew

            # registration and type
            if sector.reg and sector.type_ and sector.reg != last_reg:
                output.append(f"{sector.reg}:{sector.type_}")
                last_reg = sector.reg

            # sector
            output.append(
                f"{sector.from_}/{sector.to} "
                f"{sector.act_start:%H%M}/{sector.act_finish:%H%M}")
        output.append("")
    return "\n".join(output)


def csv(
        duties: List[Duty],
        crews: Dict[str, tuple[CrewMember, ...]],
        fo: bool
) -> str:
    output = io.StringIO(newline='')
    fieldnames = ['Off Blocks', 'On Blocks', 'Origin', 'Destination',
                  'Registration', 'Type', 'Captain', 'Role', 'Crew', 'Night']
    fieldname_map = (('Off Blocks', 'act_start'), ('On Blocks', 'act_finish'),
                     ('Origin', 'from_'), ('Destination', 'to'),
                     ('Registration', 'reg'), ('Type', 'type_'))
    writer = libcsv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction='ignore',
        dialect='unix')
    writer.writeheader()
    for duty in duties:
        if not duty.sectors:
            continue
        for sector in duty.sectors:
            if (sector.flags != SectorFlags.NONE
                    or not (sector.act_start and sector.act_finish)):
                continue
            sec_dict = sector._asdict()
            for fn, sfn in fieldname_map:
                sec_dict[fn] = sec_dict[sfn]
            sec_dict['Role'] = 'p1s' if fo else 'p1'
            crewlist = crews.get(sector.crewlist_id, tuple())
            sec_dict['Captain'] = 'Self'
            if fo and crewlist and crewlist[0].role == 'CP':
                sec_dict['Captain'] = crewlist[0].name
            crewstr = "; ".join([f"{X[1]}:{clean(X[0])}" for X in crewlist])
            if (not sector.type_ and len(sector.crewlist_id) > 3
                    and sector.crewlist_id[-3:] in ("319", "320", "321")):
                sec_dict['Type'] = f"{sector.crewlist_id[-3:]}"
            sec_dict['Crew'] = crewstr
            try:
                night_duration = nightcalc.night_duration(
                    nvecs[sector.from_], nvecs[sector.to],
                    sector.act_start, sector.act_finish)
                duration = (
                    sector.act_finish - sector.act_start).total_seconds() / 60
                sec_dict['Night'] = round(night_duration / duration, 3)
            except KeyError:  # raised by nvecs if airfields not found
                sec_dict['Night'] = ""
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

ical_datetime = "{:%Y%m%dT%H%M%SZ}"


def _build_dict(duty: Duty) -> Dict[str, str]:
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
            if sector.flags & SectorFlags.QUASI:
                airports.append(sector.name)
            elif sector.flags & SectorFlags.POSITIONING:
                airports.append("[psn]")
            if sector.to:
                airports.append(sector.to)
            off, on = sector.sched_start, sector.sched_finish
            from_to = ""
            if sector.from_ and sector.to:
                from_to = f"{sector.from_}/{sector.to} "
            sector_strings.append(
                f"{off:%H:%M}z-{on:%H:%M}z {sector.name} "
                f"{from_to}"
                f"{sector.reg if sector.reg else ''}")
    if from_:
        airports = [from_] + airports
    event["sectors"] = "DESCRIPTION:{}\r\n".format(
        "\\n\r\n ".join(sector_strings))
    event["uid"] = "{}{}@HURSTS.ORG.UK".format(
        duty.start.isoformat(), "".join(airports))
    event["route"] = "-".join(airports)
    event["modified"] = ical_datetime.format(dt.datetime.utcnow())
    return event


def ical(duties: List[Duty]) -> str:
    events = []
    for duty in duties:
        d = _build_dict(duty)
        events.append(vevent.format(**d))
    return vcalendar.format("\r\n".join(events))
