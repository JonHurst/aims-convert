import unittest
import datetime

import aims.roster as roster
from aims.roster import Duty, Sector, CrewMember

crew = ('CP - 0000 - CAPTAIN THE',
        'FO - 0001 - FO THE',
        'PU - 8000 - PU THE',
        'FA - 8001 - FA A')

crew_result = (
    CrewMember(name='CAPTAIN THE', role='CP'),
    CrewMember(name='FO THE', role='FO'),
    CrewMember(name='PU THE', role='PU'),
    CrewMember(name='FA A', role='FA'))


class Test_duties(unittest.TestCase):

    def test_standard(self):
        src = (((),
                ('02/06/2023 Fri',),
                ('2867 [320]', '2868 [320]', '239 [320]', '240 [320]'),
                ('BRS  - LIS', 'LIS  - BRS', 'BRS  - NCL', 'NCL  - BRS'),
                ('05:00',),
                ('06:00 - A08:36', 'A09:43 - A12:04',
                 'A12:52 - A13:58', 'A14:32 - A15:31'),
                ('16:01',),
                ('07:02',),
                ('11:01',),
                (), crew, ()), )
        expected = (Duty(
            code=None,
            start=datetime.datetime(2023, 6, 2, 5, 0),
            finish=datetime.datetime(2023, 6, 2, 16, 1),
            sectors=(Sector(
                name='2867', reg=None, type_='320',
                from_='BRS', to='LIS',
                off=datetime.datetime(2023, 6, 2, 6, 0),
                on=datetime.datetime(2023, 6, 2, 8, 36),
                quasi=False, position=False),
                     Sector(name='2868', reg=None, type_='320',
                            from_='LIS', to='BRS',
                            off=datetime.datetime(2023, 6, 2, 9, 43),
                            on=datetime.datetime(2023, 6, 2, 12, 4),
                            quasi=False, position=False),
                     Sector(name='239', reg=None, type_='320',
                            from_='BRS', to='NCL',
                            off=datetime.datetime(2023, 6, 2, 12, 52),
                            on=datetime.datetime(2023, 6, 2, 13, 58),
                            quasi=False, position=False),
                     Sector(name='240', reg=None, type_='320',
                            from_='NCL', to='BRS',
                            off=datetime.datetime(2023, 6, 2, 14, 32),
                            on=datetime.datetime(2023, 6, 2, 15, 31),
                            quasi=False, position=False)),
            crew=crew_result), )
        self.assertEqual(roster._duties(src), expected)

    def test_all_day_event(self):
        src = (
            ((),
             ('04/06/2023 Sun',),
             ('D/O',),
             ('Day off',),
             (), (), (), (), (), (), (), ()),
            ((),
             ('05/06/2023', 'Mon'),
             ('P/T',),
             ('Part time',),
             (), (), (), (), (), (), (), ())
        )
        expected = (
            Duty(code='D/O',
                 start=datetime.datetime(2023, 6, 4, 0, 0),
                 finish=None, sectors=(), crew=()),
            Duty(code='P/T', start=datetime.datetime(2023, 6, 5, 0, 0),
                 finish=None, sectors=(), crew=()))
        self.assertEqual(roster._duties(src), expected)
