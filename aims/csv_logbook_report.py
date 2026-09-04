import datetime as dt
from csv import DictReader

from aims.data_structures import Duty, Sector, CrewMember, AllDayEvent


HEADER = ("Date,Flight,DepPlace,DepTime,ArrPlace,ArrTime,ACType,Reg,"
          "FltTime,PicName,TKoffsDay,TKoffsNight,LandsDay,LandsNight,"
          "PIC,CoPlt,Instr,SimTime,SimType")


def _sector(record: dict[str, str]) -> Sector:
    date = dt.datetime.strptime(record["Date"], "%d/%m/%y").date()
    off = dt.datetime.combine(
        date,
        dt.datetime.strptime(record["DepTime"], "%H:%M").time())
    on = dt.datetime.combine(
        date,
        dt.datetime.strptime(record["ArrTime"], "%H:%M").time())
    if on < off:
        on += dt.timedelta(1)
    return Sector(
        name=record["Flight"],
        reg=record["Reg"],
        type_=record["ACType"],
        from_=record["DepPlace"],
        to=record["ArrPlace"],
        off=off,
        on=on,
        quasi=False,
        position=False,
        crew=(CrewMember(record['PicName'], "CP"),)
        )


def _duty(sectors: tuple[Sector, ...]) -> Duty:
    lowest_off = min([X.off for X in sectors])
    highest_on = max([X.on for X in sectors])
    return Duty(lowest_off - dt.timedelta(hours=1),
                highest_on + dt.timedelta(minutes=30),
                sectors)


def duties(csv) -> tuple[tuple[Duty, ...], tuple[AllDayEvent, ...]]:
    if not csv.startswith(HEADER):
        return ((), ())
    sectors: list[Sector] = []
    for record in DictReader(csv.splitlines()):
        if record["SimTime"]:
            pass # a sim sector
        else:
            sectors.append(_sector(record))
    if len(sectors) == 0:
        return ((), ())
    groups = [[sectors[0]]]
    last_on = sectors[0].on
    for sector in sectors[1:]:
        if sector.off - last_on > dt.timedelta(hours=10):
            groups.append([sector])
        else:
            groups[-1].append(sector)
        last_on = sector.on
    return (tuple(_duty(tuple(X)) for X in groups), ())
