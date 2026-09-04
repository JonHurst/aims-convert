import unittest
import datetime as dt

import aims.csv_logbook_report as report
from aims.data_structures import Duty, Sector, CrewMember


class TestDuties(unittest.TestCase):

    def test_standard(self):
        src = """\
Date,Flight,DepPlace,DepTime,ArrPlace,ArrTime,ACType,Reg,FltTime,PicName,TKoffsDay,TKoffsNight,LandsDay,LandsNight,PIC,CoPlt,Instr,SimTime,SimType
22/08/26,2831,BRS,06:29,VCE,08:33,320,G-EZPX,02:04,HURST,,,,,02:04,,,,
22/08/26,2832,VCE,09:21,BRS,11:47,320,G-EZPX,02:26,HURST,,,,,02:26,,,,
23/08/26,2829,BRS,23:00,JSI,01:00,321,G-UZLT,03:16,HURST,,,,,03:16,,,,
09/11/25,,LGW,06:30,LGW,10:30,319,,,,,,,,,,,04:00,E2D1
"""
        s1 = Sector("2831", "G-EZPX", "320", "BRS", "VCE",
                    dt.datetime(2026, 8, 22, 6, 29),
                    dt.datetime(2026, 8, 22, 8, 33),
                    False, False,
                    (CrewMember("HURST", "CP"),))
        s2 = Sector("2832", "G-EZPX", "320", "VCE", "BRS",
                    dt.datetime(2026, 8, 22, 9, 21),
                    dt.datetime(2026, 8, 22, 11, 47),
                    False, False,
                    (CrewMember("HURST", "CP"),))
        s3 = Sector("2829", "G-UZLT", "321", "BRS", "JSI",
                    dt.datetime(2026, 8, 23, 23, 0),
                    dt.datetime(2026, 8, 24, 1, 0),
                    False, False,
                    (CrewMember("HURST", "CP"),))
        expected = (
            (Duty(
                dt.datetime(2026, 8, 22, 5, 29),
                dt.datetime(2026, 8, 22, 12, 17),
                (s1, s2)),
            Duty(
                dt.datetime(2026, 8, 23, 22, 0),
                dt.datetime(2026, 8, 24, 1, 30),
                (s3,))),
            ())
        self.assertEqual(report.duties(src), expected)

    def test_empty(self):
        src = """\
Date,Flight,DepPlace,DepTime,ArrPlace,ArrTime,ACType,Reg,FltTime,PicName,TKoffsDay,TKoffsNight,LandsDay,LandsNight,PIC,CoPlt,Instr,SimTime,SimType
"""
        self.assertEqual(report.duties(src), ((), ()))

    def test_bad(self):
        src = "bad"
        self.assertEqual(report.duties(src), ((), ()))
        src = ""
        self.assertEqual(report.duties(src), ((), ()))
