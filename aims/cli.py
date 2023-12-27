#!/usr/bin/python3

import sys
import os
import argparse
import requests

from aims.aimstypes import Duty, Sector, SectorFlags
import aims.roster as roster
import aims.output as output


def _update_from_flightinfo(dutylist: list[Duty]) -> list[Duty]:
    retval: list[Duty] = []
    ids = []
    for duty in dutylist:
        if duty.sectors:
            ids.extend([f'{X.sched_start:%Y%m%dT%H%M}F{X.name}'
                        for X in duty.sectors
                        if X.flags == SectorFlags.NONE])
    try:
        r = requests.post(
            "https://efwj6ola8d.execute-api.eu-west-1.amazonaws.com/"
            "default/reg",
            json={'flights': ids})
        r.raise_for_status()
        regntype_map = r.json()
    except requests.exceptions.RequestException:
        return dutylist  # if anything goes wrong, just return input
    for duty in dutylist:
        if not duty.sectors:
            continue
        updated_sectors: list[Sector] = []
        for sec in duty.sectors:
            flightid = f'{sec.sched_start:%Y%m%dT%H%M}F{sec.name}'
            if flightid in regntype_map:
                reg, type_ = regntype_map[flightid]
                updated_sectors.append(sec._replace(reg=reg, type_=type_))
            else:
                updated_sectors.append(sec)
        retval.append(duty._replace(sectors=updated_sectors))
    return retval


def _args():
    parser = argparse.ArgumentParser(
        description='Access AIMS data from easyJet servers.')
    parser.add_argument('format', choices=['roster', 'freeform', 'csv', 'ical'])
    parser.add_argument('--fo', action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _args()
    s = sys.stdin.read()
    dutylist = roster.duties(s)
    if args.format == "roster":
        print(output.roster(dutylist))
    elif args.format == "freeform":
        print(output.freeform(
            _update_from_flightinfo(dutylist),
            roster.crew(s, dutylist)))
    elif args.format == "csv":
        print(output.csv(
            _update_from_flightinfo(dutylist),
            roster.crew(s, dutylist),
            args.fo))
    elif args.format == "ical":
        print(output.ical(dutylist))
    return 0


if __name__ == "__main__":
    retval = main()
    sys.exit(retval)
