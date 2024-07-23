from typing import NamedTuple, Optional
import datetime as dt


class CrewMember(NamedTuple):
    name: str
    role: str


class Sector(NamedTuple):
    name: str
    reg: Optional[str]
    type_: Optional[str]
    from_: Optional[str]
    to: Optional[str]
    off: dt.datetime
    on: dt.datetime
    quasi: bool
    position: bool
    crew: tuple[CrewMember, ...]


class Duty(NamedTuple):
    code: Optional[str]  # only all day event has code
    start: dt.datetime
    finish: Optional[dt.datetime]  # all day event has None
    sectors: tuple[Sector, ...]


class RosterException(Exception):
    "Base class"


class InputFileException(RosterException):
    "Error in input file"
