from aims.data_structures import Duty, AllDayEvent, InputFileException
import aims.roster
import aims.logbook_report
import aims.csv_logbook_report


def parse(in_: str) -> tuple[tuple[Duty, ...], tuple[AllDayEvent, ...]]:
    if in_.startswith(
            "Date,Flight,DepPlace,DepTime,ArrPlace,ArrTime,ACType,"
            "Reg,FltTime,PicName,TKoffsDay,TKoffsNight,LandsDay,"
            "LandsNight,PIC,CoPlt,Instr,SimTime,SimType"):
        return aims.csv_logbook_report.duties(in_)
    # check it's an html5 file
    html5_header = "<!DOCTYPE html><html>"
    if in_[:len(html5_header)] != html5_header:
        raise InputFileException("HTML5 header not found.")
    if in_.find("Personal&nbsp;Crew&nbsp;Schedule&nbsp;Report") != -1:
        return aims.roster.duties(in_)
    elif in_.find("Pilot&nbsp;Logbook") != -1:
        return aims.logbook_report.duties(in_)
    else:
        raise InputFileException("Report type marker not found")
