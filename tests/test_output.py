import unittest
import datetime
from freezegun import freeze_time

from aims.output import roster, efj, ical
from aims.data_structures import Duty, Sector, CrewMember, AllDayEvent


crew = (
    CrewMember(name='CAPTAIN THE', role='CP'),
    CrewMember(name='FO THE', role='FO'),
    CrewMember(name='PU THE', role='PU'),
    CrewMember(name='FA A', role='FA'))


standard_duty = Duty(
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


standby_duty = Duty(
    start=datetime.datetime(2024, 7, 25, 5, 15),
    finish=datetime.datetime(2024, 7, 25, 13, 15),
    sectors=(
        Sector(name='ESBY', reg=None, type_=None,
               from_=None, to=None,
               off=datetime.datetime(2024, 7, 25, 5, 15),
               on=datetime.datetime(2024, 7, 25, 13, 15),
               quasi=True, position=False, crew=()), ))


standby_before_flight = Duty(
    start=datetime.datetime(2023, 7, 2, 11, 45),
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
               crew=crew),
        Sector(name='228', reg=None, type_='319',
               from_='BFS', to='BRS',
               off=datetime.datetime(2023, 7, 2, 17, 56),
               on=datetime.datetime(2023, 7, 2, 18, 56),
               quasi=False, position=False,
               crew=crew)))


loe_day1 = Duty(
    start=datetime.datetime(2023, 6, 19, 14, 30),
    finish=datetime.datetime(2023, 6, 19, 18, 0),
    sectors=(
        Sector(name='TAXI227', reg=None, type_=None,
               from_='BRS', to='LGW',
               off=datetime.datetime(2023, 6, 19, 14, 30),
               on=datetime.datetime(2023, 6, 19, 18, 0),
               quasi=True, position=True, crew=()),))


loe_day2 = Duty(
    start=datetime.datetime(2023, 6, 20, 12, 0),
    finish=datetime.datetime(2023, 6, 20, 18, 30),
    sectors=(
        Sector(name='LOE', reg=None, type_=None,
               from_=None, to=None,
               off=datetime.datetime(2023, 6, 20, 13, 30),
               on=datetime.datetime(2023, 6, 20, 17, 30),
               quasi=True, position=False, crew=()),))


loe_day3 = Duty(
    start=datetime.datetime(2023, 6, 21, 8, 0),
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
               quasi=True, position=True, crew=())))


class TestRoster(unittest.TestCase):

    def test_standard(self):
        self.assertEqual(
            roster((standard_duty, standby_duty)),
            "02/06/2023 06:00-17:01 BRS-LIS-BRS-NCL-BRS 7:02/11:01\n"
            "25/07/2024 06:15-14:15 ESBY 0:00/8:00")

    def test_standby_before_flight(self):
        self.assertEqual(
            roster((standby_before_flight, )),
            "02/07/2023 12:45-14:20 LSBY 0:00/1:35\n"
            "02/07/2023 14:20-15:00 ADTY 0:00/0:40\n"
            "02/07/2023 15:00-20:26 BRS-BFS-BRS 2:09/5:26")

    def test_loe(self):
        self.assertEqual(
            roster((loe_day1, loe_day2, loe_day3)),
            "19/06/2023 15:30-19:00 TAXI227 0:00/3:30\n"
            "20/06/2023 13:00-14:30 Brief 0:00/1:30\n"
            "20/06/2023 14:30-18:30 LOE 0:00/4:00\n"
            "20/06/2023 18:30-19:30 Debrief 0:00/1:00\n"
            "21/06/2023 09:00-10:30 Brief 0:00/1:30\n"
            "21/06/2023 10:30-14:30 FFST 0:00/4:00\n"
            "21/06/2023 14:30-16:00 Debrief 0:00/1:30\n"
            "21/06/2023 16:00-19:30 TAXI72 0:00/3:30")

    def test_empty(self):
        self.assertEqual(roster(()), "")


class TestEFJ(unittest.TestCase):

    def test_standard(self):
        self.assertEqual(
            efj((standard_duty, standby_duty)),
            "2023-06-02\n"
            "0500/1601\n"
            "{ CP:Captain The, FO:Fo The, PU:Pu The, FA:Fa A }\n"
            "?-????:320\n"
            "BRS/LIS 0600/0836\n"
            "LIS/BRS 0943/1204\n"
            "BRS/NCL 1252/1358\n"
            "NCL/BRS 1432/1531\n\n"
            "2024-07-25\n"
            "0515/1315 #ESBY\n")

    def test_standby_before_flight(self):
        self.assertEqual(
            efj((standby_before_flight, )),
            "2023-07-02\n"
            "1145/1926\n"
            "{ CP:Captain The, FO:Fo The, PU:Pu The, FA:Fa A }\n"
            "?-????:319\n"
            "BRS/BFS 1614/1723\n"
            "BFS/BRS 1756/1856\n")

    def test_loe(self):
        self.assertEqual(
            efj((loe_day1, loe_day2, loe_day3)),
            "2023-06-19\n"
            "1430/1800 #TAXI227\n"
            "\n"
            "2023-06-20\n"
            "1200/1830 #LOE\n"
            "\n"
            "2023-06-21\n"
            "0800/1830\n")

    def test_empty(self):
        self.assertEqual(efj(()), "")


@freeze_time("2024-01-01")
class Test_ical(unittest.TestCase):

    def test_standard(self):
        expected = ("BEGIN:VCALENDAR\r\n"
                    "VERSION:2.0\r\n"
                    "PRODID:hursts.org.uk\r\n"
                    "BEGIN:VEVENT\r\n"
                    "UID:2023-06-02T05:00:00BRSLISBRSNCLBRS@HURSTS.ORG.UK\r\n"
                    "DTSTAMP:20240101T000000Z\r\n"
                    "DTSTART:20230602T050000Z\r\n"
                    "DTEND:20230602T160100Z\r\n"
                    "SUMMARY:BRS-LIS-BRS-NCL-BRS\r\n"
                    "DESCRIPTION:06:00z-08:36z 2867 BRS/LIS \\n\r\n"
                    " 09:43z-12:04z 2868 LIS/BRS \\n\r\n"
                    " 12:52z-13:58z 239 BRS/NCL \\n\r\n"
                    " 14:32z-15:31z 240 NCL/BRS \r\n"
                    "LAST-MODIFIED:20240101T000000Z\r\n"
                    "END:VEVENT\r\n"
                    "END:VCALENDAR\r\n")
        self.assertEqual(ical((standard_duty, ), ()), expected)

    def test_all_day_event(self):
        expected = ("BEGIN:VCALENDAR\r\n"
                    "VERSION:2.0\r\n"
                    "PRODID:hursts.org.uk\r\n"
                    "BEGIN:VEVENT\r\n"
                    "UID:2024-01-02P/T@HURSTS.ORG.UK\r\n"
                    "DTSTAMP:20240101T000000Z\r\n"
                    "DTSTART;VALUE=DATE:20240102\r\n"
                    "SUMMARY:P/T\r\n"
                    "TRANSP:TRANSPARENT\r\n"
                    "LAST-MODIFIED:20240101T000000Z\r\n"
                    "END:VEVENT\r\n"
                    "END:VCALENDAR\r\n")
        self.assertEqual(
            ical((), (AllDayEvent(datetime.date(2024, 1, 2), "P/T"), )),
            expected)
