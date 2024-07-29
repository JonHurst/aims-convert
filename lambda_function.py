import json

from aims.parse import parse
import aims.output as output
from aims.data_structures import RosterException


def lambda_handler(event, context):
    data = json.loads(event["body"])
    in_ = data["roster"]
    format = data["format"]
    options = data["options"]
    try:
        duties, ade = parse(in_)
        if format == "csv":
            out = output.csv(duties)
        elif format == "roster":
            out = output.roster(duties)
        elif format == "efj":
            out = output.efj(duties)
        elif format == "ical":
            out = output.ical(duties, ade if "ade" in options else ())
        else:
            out = "Not implemented"
    except RosterException as e:
        out = str(e)
    return {
        'statusCode': 200,
        'body': json.dumps(out)
    }
