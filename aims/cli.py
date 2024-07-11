#!/usr/bin/python3

import sys
import argparse

import aims.roster_v2 as roster
import aims.output as output


def _args():
    parser = argparse.ArgumentParser(
        description=(
            'Process an AIMS detailed roster into various useful formats.'))
    parser.add_argument('format',
                        choices=['roster', 'efj', 'csv', 'ical'])
    parser.add_argument('--ade', action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _args()
    data = roster.extract(sys.stdin.read())
    duties = roster.duties(data)
    if args.format == "roster":
        print(output.roster(duties))
    elif args.format == "efj":
        print(output.efj(duties))
    elif args.format == "csv":
        print(output.csv(duties))
    elif args.format == "ical":
        ade = roster.all_day_events(data) if args.ade else ()
        print(output.ical(duties, ade))
    return 0


if __name__ == "__main__":
    retval = main()
    sys.exit(retval)
