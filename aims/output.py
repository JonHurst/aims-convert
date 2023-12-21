#!/usr/bin/python3

from dateutil import tz
import datetime
import math
from typing import List, Dict

from aims.aimstypes import Duty, SectorFlags, CrewMember


def roster(duties: List[Duty]) -> str:
    output = []
    for duty in duties:
        if not duty.sectors: continue
        start, end = [X.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())
                      for X in (duty.start, duty.finish)]
        duration = int((end - start).total_seconds()) // 60
        from_ = None
        airports = []
        block = 0
        for sector in duty.sectors:
            if not from_ and sector.from_: from_ = sector.from_
            if sector.flags & SectorFlags.QUASI:
                airports.append(sector.name)
            elif sector.flags & SectorFlags.POSITIONING:
                airports.append("[psn]")
            else:
                off, on = sector.sched_start, sector.sched_finish
                block += int((on - off).total_seconds()) // 60
            if sector.to: airports.append(sector.to)
        if from_: airports = [from_] + airports
        duration_str = f"{duration // 60}:{duration % 60:02d}"
        block_str = f"{block // 60}:{block % 60:02d}"
        output.append(f"{start:%d/%m/%Y %H:%M}-{end:%H:%M} "
                      f"{'-'.join(airports)} {block_str}/{duration_str}")
    return "\n".join(output)


sunset_dec21 = datetime.datetime(1, 1, 1, 15, 53)
sunset_jun21 = datetime.datetime(1, 1, 1, 21, 21)
sunset_maxoffset = (sunset_dec21 - sunset_jun21) / 2
sunset_mean = sunset_jun21 + sunset_maxoffset
sunrise_dec21 = datetime.datetime(1, 1, 1, 8, 4)
sunrise_jun21 = datetime.datetime(1, 1, 1, 4, 43)
sunrise_maxoffset = (sunrise_dec21 - sunrise_jun21) / 2
sunrise_mean = sunrise_jun21 + sunrise_maxoffset


def _approx_night(d):
    """Returns a tuple consisting of two datetime.time objects
    representing (APPROX_SUNSET, APPROX_SUNRISE) for the date
    represented by datetime.date object D"""
    days_difference = (d.replace(2) - datetime.datetime(1, 12, 21)).days
    offset_factor = math.cos((days_difference * 2 * math.pi) / 365)
    sunset = sunset_mean + (sunset_maxoffset * int(offset_factor * 10000)) // 10000
    sunrise = sunrise_mean + (sunrise_maxoffset * int(offset_factor * 10000)) // 10000
    return (sunset.time(), sunrise.time())


def freeform(duties: List[Duty], crews: Dict[str, List[CrewMember]]
) -> str:
    output = []
    for duty in duties:
        if not duty.sectors: continue
        output.append(f"{duty.start:%Y-%m-%d}")
        comment = ""
        if (len(duty.sectors) == 1 and
            (duty.sectors[0].flags & SectorFlags.QUASI)):
            comment = f" #{duty.sectors[0].name}"
        output.append(f"{duty.start:%H%M}/{duty.finish:%H%M}{comment}")
        reg = None
        last_crew = None
        for sector in duty.sectors:
            if not sector.act_start or sector.flags != SectorFlags.NONE:
                continue

            #crewlist
            if sector.crewlist_id and sector.crewlist_id in crews:
                crew = [f"{X[1]}:{X[0]}" for X in crews[sector.crewlist_id]]
                if crew != last_crew:
                    output.append(f"{{ {', '.join(crew)} }}")
                    last_crew = crew

            #night
            sunset, sunrise = _approx_night(sector.act_finish)
            mid_duty_time = (sector.act_start +
                             (sector.act_finish - sector.act_start) // 2)
            night = ""
            if mid_duty_time.time() > sunset or mid_duty_time.time() < sunrise:
                night = " n"

            #registration and type
            if sector.reg and reg != sector.reg:
                #the crewlist_id appears to have the type as the last three
                #characters -- this might turn out to be a wild assumption
                #but we'll use it until proven to be a bad idea.
                type_ = "???"
                if sector.type_:
                    type_ = sector.type_
                elif (len(sector.crewlist_id) > 3 and
                    sector.crewlist_id[-3:] in ("319", "320", "321")):
                    type_ = f"A{sector.crewlist_id[-3:]}"
                output.append(f"{sector.reg}:{type_}")
                reg = sector.reg

            #sector
            output.append(
                f"{sector.from_}/{sector.to} "
                f"{sector.act_start:%H%M}/{sector.act_finish:%H%M} "
                f"{night}")
        output.append("")
    return "\n".join(output)
