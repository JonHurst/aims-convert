import json

import aims.roster as roster
import aims.output as output


def lambda_handler(event, context):
    data = json.loads(event["body"])
    in_ = data["roster"]
    format = data["format"]
    options = data["options"]
    try:
        lines = roster.lines(in_)
        columns = roster.columns(lines)
        sectors = roster.sectors(columns)
        if format == "csv":
            out = output.csv(
                sectors,
                roster.crew_dict(lines))
        elif format == "roster":
            out = output.roster(sectors)
        elif format == "efj":
            out = output.efj(
                sectors,
                roster.crew_dict(lines))
        elif format == "ical":
            ade = roster.all_day_events(columns) if "ade" in options else ()
            out = output.ical(sectors, ade)
        else:
            out = "Not implemented"
    except roster.RosterException as e:
        out = str(e)
    return {
        'statusCode': 200,
        'body': json.dumps(out)
    }
