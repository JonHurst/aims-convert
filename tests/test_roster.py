import unittest
import datetime

import aims.roster as roster
from aims.data_structures import (
    Duty, Sector, CrewMember, AllDayEvent, InputFileException
)

crew = ('CP - 0000 - CAPTAIN THE',
        'FO - 0001 - FO THE',
        'PU - 8000 - PU THE',
        'FA - 8001 - FA', 'A',
        'FA - PAX - 8002 - POSITIONER')

crew_result = (
    CrewMember(name='CAPTAIN THE', role='CP'),
    CrewMember(name='FO THE', role='FO'),
    CrewMember(name='PU THE', role='PU'),
    CrewMember(name='FA A', role='FA'))


class Test_duty(unittest.TestCase):

    def test_standard(self):
        src = ((),
               ('02/06/2023 Fri',),
               ('2867 [320]', '2868 [320]', '239 [320]', '240 [320]'),
               ('BRS  - LIS', 'LIS  - BRS', 'BRS  - NCL', 'NCL  - BRS'),
               ('05:00',),
               ('06:00 - A08:36', 'A09:43 - A12:04',
                'A12:52 - A13:58', 'E14:32 - E15:31'),
               ('16:01',),
               ('07:02',),
               ('11:01',),
               (), crew, ())
        expected = Duty(
            start=datetime.datetime(2023, 6, 2, 5, 0),
            finish=datetime.datetime(2023, 6, 2, 16, 1),
            sectors=(
                Sector(name='2867', reg=None, type_='320',
                       from_='BRS', to='LIS',
                       off=datetime.datetime(2023, 6, 2, 6, 0),
                       on=datetime.datetime(2023, 6, 2, 8, 36),
                       quasi=False, position=False, crew=crew_result),
                Sector(name='2868', reg=None, type_='320',
                       from_='LIS', to='BRS',
                       off=datetime.datetime(2023, 6, 2, 9, 43),
                       on=datetime.datetime(2023, 6, 2, 12, 4),
                       quasi=False, position=False, crew=crew_result),
                Sector(name='239', reg=None, type_='320',
                       from_='BRS', to='NCL',
                       off=datetime.datetime(2023, 6, 2, 12, 52),
                       on=datetime.datetime(2023, 6, 2, 13, 58),
                       quasi=False, position=False, crew=crew_result),
                Sector(name='240', reg=None, type_='320',
                       from_='NCL', to='BRS',
                       off=datetime.datetime(2023, 6, 2, 14, 32),
                       on=datetime.datetime(2023, 6, 2, 15, 31),
                       quasi=False, position=False, crew=crew_result))
            )
        self.assertEqual(roster._duty(src), expected)

    def test_loe(self):
        src = (
            ((), ('19/06/2023', 'Mon'),
             ('TAXI227',), ('*BRS  - LGW',),
             ('14:30',), ('14:30 - 18:00',), ('18:00',),
             (), ('03:30',), (), ('CP - PAX - 0000 - CAPTAIN THE',),
             ()),
            ((), ('20/06/2023 Tue',),
             ('LOE',), ('LOE Simulator',),
             ('12:00',), ('13:30 - 17:30',), ('18:30',),
             (), ('06:30',), ('M',), (), ()),
            ((), ('21/06/2023', 'Wed'),
             ('FFST', 'TAXI72'), ('LGW  - LGW', '*LGW  - BRS'),
             ('08:00',), ('09:30 - 13:30', '15:00 - 18:30'), ('18:30',),
             (), ('10:30',), (), ('CP - PAX - 0000 - CAPTAIN THE',),
             ()))
        expected = (
            Duty(start=datetime.datetime(2023, 6, 19, 14, 30),
                 finish=datetime.datetime(2023, 6, 19, 18, 0),
                 sectors=(
                     Sector(name='TAXI227', reg=None, type_=None,
                            from_='BRS', to='LGW',
                            off=datetime.datetime(2023, 6, 19, 14, 30),
                            on=datetime.datetime(2023, 6, 19, 18, 0),
                            quasi=True, position=True, crew=()),)),
            Duty(start=datetime.datetime(2023, 6, 20, 12, 0),
                 finish=datetime.datetime(2023, 6, 20, 18, 30),
                 sectors=(
                     Sector(name='LOE', reg=None, type_=None,
                            from_=None, to=None,
                            off=datetime.datetime(2023, 6, 20, 13, 30),
                            on=datetime.datetime(2023, 6, 20, 17, 30),
                            quasi=True, position=False, crew=()),)),
            Duty(start=datetime.datetime(2023, 6, 21, 8, 0),
                 finish=datetime.datetime(2023, 6, 21, 18, 30),
                 sectors=(
                     Sector(name='FFST', reg=None, type_=None,
                            from_='LGW', to='LGW',
                            off=datetime.datetime(2023, 6, 21, 9, 30),
                            on=datetime.datetime(2023, 6, 21, 13, 30),
                            quasi=True, position=False, crew=()),
                     Sector(name='TAXI72', reg=None, type_=None,
                            from_='LGW', to='BRS',
                            off=datetime.datetime(2023, 6, 21, 15, 0),
                            on=datetime.datetime(2023, 6, 21, 18, 30),
                            quasi=True, position=True, crew=()))))
        for c in range(3):
            self.assertEqual(roster._duty(src[c]), expected[c])

    def test_standby(self):
        src = ((), ('25/07/2024 Thu',),
               ('ESBY',), ('Early Standby',),
               (),  ('05:15 - 13:15',),  (),
               (),  ('08:00',),
               (),  crew,  ())
        expected = Duty(start=datetime.datetime(2024, 7, 25, 5, 15),
                        finish=datetime.datetime(2024, 7, 25, 13, 15),
                        sectors=(
                            Sector(name='ESBY', reg=None, type_=None,
                                   from_=None, to=None,
                                   off=datetime.datetime(2024, 7, 25, 5, 15),
                                   on=datetime.datetime(2024, 7, 25, 13, 15),
                                   quasi=True, position=False, crew=()), ))
        self.assertEqual(roster._duty(src), expected)

    def test_standby_before_flights(self):
        src = ((),
               ('02/07/2023 Sun',),
               ('LSBY', 'ADTY', '227 [319]', '228 [319]'),
               ('BRS  - BRS', 'BRS  - BRS', 'BRS  - BFS', 'BFS  - BRS'),
               ('14:00',),  # note this is after 11:45!
               ('11:45 - 13:20', '13:20 - 14:00',
                'A16:14 - A17:23', 'A17:56 - A18:56'),
               ('19:26',),  ('02:09',),  ('07:41',),  (),  crew, ())
        expected = Duty(start=datetime.datetime(2023, 7, 2, 11, 45),
                        finish=datetime.datetime(2023, 7, 2, 19, 26),
                        sectors=(
                            Sector(name='LSBY', reg=None, type_=None,
                                   from_='BRS', to='BRS',
                                   off=datetime.datetime(2023, 7, 2, 11, 45),
                                   on=datetime.datetime(2023, 7, 2, 13, 20),
                                   quasi=True, position=False,
                                   crew=()),
                            Sector(name='ADTY', reg=None, type_=None,
                                   from_='BRS', to='BRS',
                                   off=datetime.datetime(2023, 7, 2, 13, 20),
                                   on=datetime.datetime(2023, 7, 2, 14, 0),
                                   quasi=True, position=False,
                                   crew=()),
                            Sector(name='227', reg=None, type_='319',
                                   from_='BRS', to='BFS',
                                   off=datetime.datetime(2023, 7, 2, 16, 14),
                                   on=datetime.datetime(2023, 7, 2, 17, 23),
                                   quasi=False, position=False,
                                   crew=crew_result),
                            Sector(name='228', reg=None, type_='319',
                                   from_='BFS', to='BRS',
                                   off=datetime.datetime(2023, 7, 2, 17, 56),
                                   on=datetime.datetime(2023, 7, 2, 18, 56),
                                   quasi=False, position=False,
                                   crew=crew_result))
                        )
        self.assertEqual(roster._duty(src), expected)

    def test_over_midnight(self):
        src = ((), ('25/06/2023 Sun',),
               ('239 [320]', '240 [320]', '2873 [320]', '2874 [320]'),
               ('BRS  - NCL', 'NCL  - BRS', 'BRS  - FAO', 'FAO  - BRS'),
               ('14:00',),
               ('A15:24 - A16:19', 'A17:27 - A18:41',
                'A19:21 - A21:56', 'A22:33 - A00:57⁺¹/00:24'),
               ('01:27⁺¹',), ('07:08',), ('11:27',), ('M',),
               crew, ())
        expected = Duty(start=datetime.datetime(2023, 6, 25, 14, 0),
                        finish=datetime.datetime(2023, 6, 26, 1, 27),
                        sectors=(
                            Sector(name='239', reg=None, type_='320',
                                   from_='BRS', to='NCL',
                                   off=datetime.datetime(2023, 6, 25, 15, 24),
                                   on=datetime.datetime(2023, 6, 25, 16, 19),
                                   quasi=False, position=False,
                                   crew=crew_result),
                            Sector(name='240', reg=None, type_='320',
                                   from_='NCL', to='BRS',
                                   off=datetime.datetime(2023, 6, 25, 17, 27),
                                   on=datetime.datetime(2023, 6, 25, 18, 41),
                                   quasi=False, position=False,
                                   crew=crew_result),
                            Sector(name='2873', reg=None, type_='320',
                                   from_='BRS', to='FAO',
                                   off=datetime.datetime(2023, 6, 25, 19, 21),
                                   on=datetime.datetime(2023, 6, 25, 21, 56),
                                   quasi=False, position=False,
                                   crew=crew_result),
                            Sector(name='2874', reg=None, type_='320',
                                   from_='FAO', to='BRS',
                                   off=datetime.datetime(2023, 6, 25, 22, 33),
                                   on=datetime.datetime(2023, 6, 26, 0, 57),
                                   quasi=False, position=False,
                                   crew=crew_result))
                        )
        self.assertEqual(roster._duty(src), expected)

    def test_emptyrow(self):
        with self.assertRaises(InputFileException):
            roster._duty(())
        with self.assertRaises(InputFileException):
            roster._duty(() * 12)

    def test_bad_date(self):
        with self.assertRaises(InputFileException):
            roster._duty(((), ('32/07/2024 Thu',),
                          ('ESBY',), ('Early Standby',),
                          (),  ('24:00 - 13:15',),  (),
                          (),  ('08:00',),
                          (),  (),  ()))

    def test_bad_time(self):
        with self.assertRaises(InputFileException):
            roster._duty(((), ('25/07/2024 Thu',),
                          ('ESBY',), ('Early Standby',),
                          (),  ('24:00 - 13:15',),  (),
                          (),  ('08:00',),
                          (),  (),  ()))


class Test_ade(unittest.TestCase):

    def test_simple(self):
        src = ((),
               ('04/06/2023 Sun',),
               ('D/O',),
               ('Day off',),
               (), (), (), (), (), (), (), ())
        self.assertEqual(roster._ade(src),
                         AllDayEvent(datetime.date(2023, 6, 4), "D/O"))
