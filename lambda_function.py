import json

import aims.roster as roster
import aims.output as output


def lambda_handler(event, context):
    data = json.loads(event["body"])
    in_ = data["roster"]
    format = data["format"]
    options = data["options"]
    lines = roster.lines(in_)
    columns = roster.columns(lines)
    sectors = roster.sectors(columns)
    if format == "csv":
        out = output.csv(
            sectors,
            roster.crew_dict(lines),
            "fo" in options)
    elif format == "roster":
        out = output.roster(sectors)
    elif format == "freeform":
        out = output.freeform(
            sectors,
            roster.crew_dict(lines))
    elif format == "ical":
        ade = roster.all_day_events(columns) if "ade" in options else ()
        out = output.ical(sectors, ade)
    else:
        out = "Not implemented"
    return {
        'statusCode': 200,
        'body': json.dumps(out)
    }
