import requests
from aims.roster import Duty, Sector


def sector_id(sector: Sector) -> str:
    return f'{sector.off:%Y%m%dT%H%M}F{sector.name}'


def airframes(dutylist: list[Duty]) -> dict[str, tuple[str, str]]:
    ids = []
    for duty in dutylist:
        if duty.sectors:
            ids.extend([sector_id(X) for X in duty.sectors if X.from_])
    try:
        r = requests.post(
            "https://efwj6ola8d.execute-api.eu-west-1.amazonaws.com/"
            "default/reg",
            json={'flights': ids})
        r.raise_for_status()
        regntype_map = r.json()
    except requests.exceptions.RequestException:
        return {}  # if anything goes wrong, just return empty dict
    return regntype_map
