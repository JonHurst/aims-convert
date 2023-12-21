#!/usr/bin/python3

import datetime
import math
from typing import List, Dict
from zoneinfo import ZoneInfo as Z

from aims.aimstypes import Duty, SectorFlags, CrewMember

UTC = Z("UTC")
LT = Z("Europe/London")


def roster(duties: List[Duty]) -> str:
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
                crew = [f"{X[1]}:{X[0]}" for X in crews[sector.crewlist_id]]
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
