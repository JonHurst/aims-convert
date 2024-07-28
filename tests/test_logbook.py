import unittest
import datetime

import aims.logbook_report as report
from aims.data_structures import Duty, Sector, CrewMember


class TestDuty(unittest.TestCase):

    def test_standard(self):
        sectors = (
            Sector(name='6053', reg='G-EZRY', type_='320',
                   from_='BRS', to='AGP',
                   off=datetime.datetime(2022, 7, 23, 11, 44),
                   on=datetime.datetime(2022, 7, 23, 14, 7),
                   quasi=False, position=False,
                   crew=(CrewMember("TEST-1", "CP"), )),
            Sector(name='6056', reg='G-EZRY', type_='320',
                   from_='AGP', to='BRS',
                   off=datetime.datetime(2022, 7, 23, 15, 0),
                   on=datetime.datetime(2022, 7, 23, 17, 41),
                   quasi=False, position=False,
                   crew=(CrewMember("TEST-2", "CP"), )))
        expected = Duty(
            start=datetime.datetime(2022, 7, 23, 10, 44),
            finish=datetime.datetime(2022, 7, 23, 18, 11),
            sectors=(Sector(name='6053', reg='G-EZRY', type_='320',
                            from_='BRS', to='AGP',
                            off=datetime.datetime(2022, 7, 23, 11, 44),
                            on=datetime.datetime(2022, 7, 23, 14, 7),
                            quasi=False, position=False,
                            crew=(CrewMember("TEST-1", "CP"), )),
                     Sector(name='6056', reg='G-EZRY', type_='320',
                            from_='AGP', to='BRS',
                            off=datetime.datetime(2022, 7, 23, 15, 0),
                            on=datetime.datetime(2022, 7, 23, 17, 41),
                            quasi=False, position=False,
                            crew=(CrewMember("TEST-2", "CP"), )))
            )
        self.assertEqual(report._duty(sectors), expected)


class TestSector(unittest.TestCase):

    def test_standard(self):
        src = ('', '23/07/22', '6053', 'BRS', '11:44', 'AGP', '14:07',
               '320', 'G-EZRY', '02:23', 'CAPTAIN THE',
               '', '', '', '', '02:23', '', '', '', '')
        expected = Sector(name='6053', reg='G-EZRY', type_='320',
                          from_='BRS', to='AGP',
                          off=datetime.datetime(2022, 7, 23, 11, 44),
                          on=datetime.datetime(2022, 7, 23, 14, 7),
                          quasi=False, position=False,
                          crew=(CrewMember("CAPTAIN THE", "CP"), ))
        self.assertEqual(report._sector(src), expected)
        src = ('', '23/07/22', '6056', 'AGP', '15:00', 'BRS', '17:41',
               '320', 'G-EZRY', '02:41', 'CAPTAIN THE',
               '', '', '', '', '02:41', '', '', '', '')
        expected = Sector(name='6056', reg='G-EZRY', type_='320',
                          from_='AGP', to='BRS',
                          off=datetime.datetime(2022, 7, 23, 15, 0),
                          on=datetime.datetime(2022, 7, 23, 17, 41),
                          quasi=False, position=False,
                          crew=(CrewMember("CAPTAIN THE", "CP"), ))
        self.assertEqual(report._sector(src), expected)

    def test_over_midnight(self):
        src = ('', '28/07/22', '6304', 'AYT', '21:28', 'BRS', '01:55',
               '321', 'G-UZMJ', '04:27', 'CAPTAIN THE',
               '', '', '', '', '04:27', '', '', '', '')
        expected = Sector(name='6304', reg='G-UZMJ', type_='321',
                          from_='AYT', to='BRS',
                          off=datetime.datetime(2022, 7, 28, 21, 28),
                          on=datetime.datetime(2022, 7, 29, 1, 55),
                          quasi=False, position=False,
                          crew=(CrewMember("CAPTAIN THE", "CP"), ))
        self.assertEqual(report._sector(src), expected)
