import unittest
import datetime

from aims.output import roster
from aims.data_structures import Duty, Sector, CrewMember


crew = (
    CrewMember(name='CAPTAIN THE', role='CP'),
    CrewMember(name='FO THE', role='FO'),
    CrewMember(name='PU THE', role='PU'),
    CrewMember(name='FA A', role='FA'))


standard_duty = Duty(
    code=None,
    start=datetime.datetime(2023, 6, 2, 5, 0),
    finish=datetime.datetime(2023, 6, 2, 16, 1),
    sectors=(
        Sector(name='2867', reg=None, type_='320',
               from_='BRS', to='LIS',
               off=datetime.datetime(2023, 6, 2, 6, 0),
               on=datetime.datetime(2023, 6, 2, 8, 36),
               quasi=False, position=False, crew=crew),
        Sector(name='2868', reg=None, type_='320',
               from_='LIS', to='BRS',
               off=datetime.datetime(2023, 6, 2, 9, 43),
               on=datetime.datetime(2023, 6, 2, 12, 4),
               quasi=False, position=False, crew=crew),
        Sector(name='239', reg=None, type_='320',
               from_='BRS', to='NCL',
               off=datetime.datetime(2023, 6, 2, 12, 52),
               on=datetime.datetime(2023, 6, 2, 13, 58),
               quasi=False, position=False, crew=crew),
        Sector(name='240', reg=None, type_='320',
               from_='NCL', to='BRS',
               off=datetime.datetime(2023, 6, 2, 14, 32),
               on=datetime.datetime(2023, 6, 2, 15, 31),
               quasi=False, position=False, crew=crew)))


all_day_duty = Duty(
    code='D/O',
    start=datetime.datetime(2023, 6, 4, 0, 0),
    finish=None, sectors=())


standby_duty = Duty(
    code=None,
    start=datetime.datetime(2024, 7, 25, 5, 15),
    finish=datetime.datetime(2024, 7, 25, 13, 15),
    sectors=(
        Sector(name='ESBY', reg=None, type_=None,
               from_=None, to=None,
               off=datetime.datetime(2024, 7, 25, 5, 15),
               on=datetime.datetime(2024, 7, 25, 13, 15),
               quasi=True, position=False, crew=()), ))


class TestRoster(unittest.TestCase):

    def test_standard(self):
        self.assertEqual(
            roster((standard_duty, all_day_duty, standby_duty)),
            "02/06/2023 06:00-17:01 BRS-LIS-BRS-NCL-BRS 7:02/11:01\n"
            "25/07/2024 06:15-14:15 ESBY 0:00/8:00")
