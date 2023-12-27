#!/usr/bin/python3

import sys
import argparse

import aims.roster as roster
import aims.output as output


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
            dutylist,
            roster.crew(s, dutylist)))
    elif args.format == "csv":
        print(output.csv(
            dutylist,
            roster.crew(s, dutylist),
            args.fo))
    elif args.format == "ical":
        print(output.ical(dutylist))
    return 0


if __name__ == "__main__":
    retval = main()
    sys.exit(retval)
