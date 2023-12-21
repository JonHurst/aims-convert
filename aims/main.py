#!/usr/bin/python3

import sys
import os
import argparse
import requests

from aims.types import Duty, Sector, SectorFlags
import aims.roster as roster
import aims.output as output


def _update_from_flightinfo(dutylist: list[Duty]) -> list[Duty]:
    retval: list[Duty] = []
    ids = []
    for duty in dutylist:
        ids.extend([f'{X.sched_start:%Y%m%dT%H%M}F{X.name}'
                    for X in duty.sectors
                    if X.flags == SectorFlags.NONE])
    try:
        r = requests.post(
            "https://efwj6ola8d.execute-api.eu-west-1.amazonaws.com/default/reg",
            json={'flights': ids})
        r.raise_for_status()
        regntype_map = r.json()
    except requests.exceptions.RequestException:
        return dutylist  # if anything goes wrong, just return input
    for duty in dutylist:
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
    parser.add_argument('format', choices=['roster', 'freeform'])
    parser.add_argument('target')
    parser.add_argument('--file', '-f', action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _args()
    s = ""
    try:
        if args.file:
            with open(args.target, encoding="utf-8") as f:
                s = f.read()
        else:
            aws_roster_path = os.environ.get("AWS_ROSTER_PATH")
            aws_authstr = os.environ.get("AWS_AUTHSTR");
            r = requests.get(
                aws_roster_path + f"roster-{args.target}.htm",
                headers={"Authorization": f"Basic {aws_authstr}"})
            r.raise_for_status()
            s = r.text
    except Exception as e:
        print("Failed to load AIMS detailed roster")
        print(e)
        return -1
    dutylist = roster.duties(s)
    if args.format == "roster":
        print(output.roster(dutylist))
    elif args.format == "freeform":
        dutylist = _update_from_flightinfo(dutylist)
        crew = roster.crew(s, dutylist)
        print(crew)
        print(output.freeform(dutylist, crew))
    return 0


if __name__ == "__main__":
    retval = main()
    sys.exit(retval)
