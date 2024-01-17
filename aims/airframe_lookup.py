import requests
from aims.roster import Sector


def sector_id(sector: Sector) -> str:
    return f'{sector.off:%Y%m%dT%H%M}F{sector.name}'


def airframes(sectors: tuple[Sector, ...]) -> dict[str, tuple[str, str]]:
    ids = [sector_id(X) for X in sectors if X.from_]
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
