from typing import NamedTuple, Optional
import datetime as dt


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


class CrewMember(NamedTuple):
    name: str
    role: str


class Duty(NamedTuple):
    code: Optional[str]  # only all day event has code
    start: dt.datetime
    finish: Optional[dt.datetime]  # all day event has None
    sectors: tuple[Sector, ...]
    crew: tuple[CrewMember, ...]


class RosterException(Exception):

    def __str__(self):
        return self.__doc__


class InputFileException(RosterException):
    "Input file does not appear to be an AIMS roster."
