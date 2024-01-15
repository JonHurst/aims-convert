#!/usr/bin/python3

import unittest
from datetime import datetime as DT
from datetime import date as D
import aims.roster as p
from aims.roster import Sector, Duty


def SDT(d, h=0, m=0):
    return DT(2021, 10, d, h, m)


def SD(d):
    return D(2021, 10, d)


class Test_sectors(unittest.TestCase):

    def test_standard(self):
        BRSFNC = ('EZS', '6245', SDT(21, 5, 30), SDT(21, 6, 34),
                  'BRS', 'FNC', SDT(21, 9, 45), '(320)')
        FNCBRS = ('EJU', '6246', SDT(21, 10, 32), 'FNC', 'BRS',
                  SDT(21, 13, 59), SDT(21, 14, 29), '(320)')
        BRSSPU = ('G\xa0EJU', '6205', SDT(22, 4, 15), SDT(22, 5, 12),
                  'BRS', 'SPU', SDT(22, 7, 56), '(320)')
        SPUBRS = ('6206', SDT(22, 13, 16), 'SPU', 'BRS',
                  SDT(22, 15, 50), SDT(22, 16, 20), '(320)', 'FO')
        SBY = ('SBY', SDT(23, 10), SDT(23, 16))
        data = ((SD(21), (BRSFNC, FNCBRS)),
                (SD(22), (BRSSPU, SPUBRS)),
                (SD(23), (SBY,)))
        expected_result = (
            Sector('6245', 'BRS', 'FNC',
                   SDT(21, 6, 34), SDT(21, 9, 45), BRSFNC),
            Sector('6246', 'FNC', 'BRS',
                   SDT(21, 10, 32), SDT(21, 13, 59), FNCBRS),
            Sector('6205', 'BRS', 'SPU',
                   SDT(22, 5, 12), SDT(22, 7, 56), BRSSPU),
            Sector('6206', 'SPU', 'BRS',
                   SDT(22, 13, 16), SDT(22, 15, 50), SPUBRS),
            Sector('SBY', None, None,
                   SDT(23, 10), SDT(23, 16), SBY))
        self.assertEqual(sorted(p.sectors(data)), sorted(expected_result))

    def test_across_midnight(self):
        SBY1 = ('SBY', SDT(17, 22))
        SBY2 = (SDT(18, 2),)
        SBY = ('SBY', SDT(17, 22), (SDT(18, 2)))
        PMI1 = ('6046', SDT(18, 21, 25), SDT(18, 21, 35), "PMI", "(A320)")
        PMI2 = ("BRS", SDT(19, 23, 55), SDT(19, 0, 25))  # n.b. dragover
        PMI = ('6046', SDT(18, 21, 25), SDT(18, 21, 35), "PMI", "(A320)",
               "BRS", SDT(19, 23, 55), SDT(19, 0, 25))
        data = ((SD(17), (SBY1,)),
                (SD(18), (SBY2, PMI1)),
                (SD(19), (PMI2,)))
        expected_result = (
            Sector('SBY', None, None, SDT(17, 22), SDT(18, 2), SBY),
            Sector('6046', "PMI", "BRS",
                   SDT(18, 21, 35), SDT(18, 23, 55), PMI))
        self.assertEqual(sorted(p.sectors(data)), sorted(expected_result))

    def test_edges(self):
        SBY2 = (SDT(18, 2),)
        SBY = ("???", SDT(18), SDT(18, 2))
        PMI1 = ('6046', SDT(18, 21, 25), SDT(18, 21, 35), "PMI", "(A320)")
        PMI = ('6046', SDT(18, 21, 25), SDT(18, 21, 35), "PMI", "(A320)",
               '???', SDT(19), SDT(19))
        data = ((SD(18), (SBY2, PMI1)),)
        expected_result = (
            Sector('???', None, None, SDT(18), SDT(18, 2), SBY),
            Sector('6046', 'PMI', '???', SDT(18, 21, 35), SDT(19), PMI))
        with self.subTest("half standby then half sector"):
            self.assertEqual(sorted(p.sectors(data)), sorted(expected_result))
        SBY1 = ('SBY', SDT(18, 21, 25))
        SBY = ('SBY', SDT(18, 21, 25), SDT(19))
        data = ((SD(18), (SBY1,)),)
        expected_result = (
            Sector('SBY', None, None, SDT(18, 21, 25), SDT(19), SBY),)
        with self.subTest("half standby only"):
            self.assertEqual(p.sectors(data), expected_result)
        PMI2 = ("BRS", SDT(19, 23, 55), SDT(19, 0, 25))  # n.b. dragover
        data = ((SD(19), (PMI2,)),)
        expected_result = (
            Sector('BRS', None, None, SDT(18, 23, 55), SDT(19, 0, 25), PMI2),)
        with self.subTest("end of half sector only"):
            self.assertEqual(p.sectors(data), expected_result)

    def test_loe_then_position(self):
        LOE1 = ("LOE", SDT(28, 19), SDT(28, 20, 30))
        LOE2 = (SDT(29, 0, 30), SDT(29, 1, 30))
        LOE = ("LOE", SDT(28, 19), SDT(28, 20, 30),
               SDT(29, 0, 30), SDT(29, 1, 30))
        POSN = ("6224", SDT(29, 16), SDT(29, 17), "*CDG", "BRS",
                SDT(29, 18, 8), SDT(29, 18, 23))
        M = ("M",)
        data = ((SD(28), (LOE1,)),
                (SD(29), (LOE2, POSN, M)))
        expected_result = (
            Sector("LOE", None, None, SDT(28, 20, 30), SDT(29, 0, 30), LOE),
            Sector("6224", "*CDG", "BRS", SDT(29, 17), SDT(29, 18, 8), POSN))
        self.assertEqual(sorted(p.sectors(data)), sorted(expected_result))

    def test_callout_to_asby_then_callout_to_fly(self):
        SBY = ("LSBY", SDT(6, 12, 40), SDT(6, 17))
        ADTY = ("ADTY", SDT(6, 17), SDT(6, 17, 45))
        BRSPMI = ("6045", SDT(6, 21, 10), "BRS", "PMI", SDT(6, 23, 22))
        PMIBRS = ("6046", SDT(7, 0, 29), "PMI", "BRS",
                  SDT(7, 2, 46), SDT(7, 3, 16))
        data = ((SD(6), (SBY, ADTY, BRSPMI)),
                (SD(7), (PMIBRS,)))
        expected_result = (
            Sector("LSBY", None, None, SDT(6, 12, 40), SDT(6, 17), SBY),
            Sector("ADTY", None, None, SDT(6, 17), SDT(6, 17, 45), ADTY),
            Sector("6045", "BRS", "PMI",
                   SDT(6, 21, 10), SDT(6, 23, 22), BRSPMI),
            Sector("6046", "PMI", "BRS",
                   SDT(7, 0, 29), SDT(7, 2, 46), PMIBRS))
        self.assertEqual(sorted(p.sectors(data)), sorted(expected_result))


class Test_duties(unittest.TestCase):

    def test_basic(self):
        data = [
            Sector('SBY', None, None, DT(2021, 5, 17, 22), DT(2021, 5, 18, 2),
                   [DT(2021, 5, 17, 22), DT(2021, 5, 18, 2)]),
            Sector('6046', "PMI", "BRS",
                   DT(2021, 5, 18, 21, 35), DT(2021, 5, 18, 23, 55),
                   [DT(2021, 5, 18, 21, 25), DT(2021, 5, 18, 21, 35),
                    DT(2021, 5, 18, 23, 55), DT(2021, 5, 19, 0, 25)]),
            Sector('6245', 'BRS', 'FNC',
                   DT(2021, 10, 21, 6, 34), DT(2021, 10, 21, 9, 45),
                   [DT(2021, 10, 21, 5, 30), DT(2021, 10, 21, 6, 34),
                    DT(2021, 10, 21, 9, 45)]),
            Sector('6246', 'FNC', 'BRS',
                   DT(2021, 10, 21, 10, 32), DT(2021, 10, 21, 13, 59),
                   [DT(2021, 10, 21, 10, 32), DT(2021, 10, 21, 13, 59),
                    DT(2021, 10, 21, 14, 29)]),
            Sector('6205', 'BRS', 'SPU',
                   DT(2021, 10, 22, 5, 12), DT(2021, 10, 22, 7, 56),
                   [DT(2021, 10, 22, 4, 15), DT(2021, 10, 22, 5, 12),
                    DT(2021, 10, 22, 7, 56),]),
            Sector('6206', 'SPU', 'BRS',
                   DT(2021, 10, 22, 13, 16), DT(2021, 10, 22, 15, 50),
                   [DT(2021, 10, 22, 13, 16), DT(2021, 10, 22, 15, 50),
                    DT(2021, 10, 22, 16, 20)])
        ]

        expected_result = [
            Duty(DT(2021, 5, 17, 22), DT(2021, 5, 18, 2), (
                Sector('SBY', None, None, DT(2021, 5, 17, 22),
                       DT(2021, 5, 18, 2),
                       [DT(2021, 5, 17, 22), DT(2021, 5, 18, 2)]),)),
            Duty(DT(2021, 5, 18, 21, 25), DT(2021, 5, 19, 0, 25), (
                Sector('6046', "PMI", "BRS",
                       DT(2021, 5, 18, 21, 35), DT(2021, 5, 18, 23, 55),
                       [DT(2021, 5, 18, 21, 25), DT(2021, 5, 18, 21, 35),
                        DT(2021, 5, 18, 23, 55), DT(2021, 5, 19, 0, 25)]),)),
            Duty(DT(2021, 10, 21, 5, 30), DT(2021, 10, 21, 14, 29), (
                Sector('6245', 'BRS', 'FNC',
                       DT(2021, 10, 21, 6, 34), DT(2021, 10, 21, 9, 45),
                       [DT(2021, 10, 21, 5, 30), DT(2021, 10, 21, 6, 34),
                        DT(2021, 10, 21, 9, 45)]),
                Sector('6246', 'FNC', 'BRS',
                       DT(2021, 10, 21, 10, 32), DT(2021, 10, 21, 13, 59),
                       [DT(2021, 10, 21, 10, 32), DT(2021, 10, 21, 13, 59),
                        DT(2021, 10, 21, 14, 29)]),)),
            Duty(DT(2021, 10, 22, 4, 15), DT(2021, 10, 22, 16, 20), (
                Sector('6205', 'BRS', 'SPU',
                       DT(2021, 10, 22, 5, 12), DT(2021, 10, 22, 7, 56),
                       [DT(2021, 10, 22, 4, 15), DT(2021, 10, 22, 5, 12),
                        DT(2021, 10, 22, 7, 56),]),
                Sector('6206', 'SPU', 'BRS',
                       DT(2021, 10, 22, 13, 16), DT(2021, 10, 22, 15, 50),
                       [DT(2021, 10, 22, 13, 16), DT(2021, 10, 22, 15, 50),
                        DT(2021, 10, 22, 16, 20)]),)),
        ]
        self.assertEqual(p.duties(data), expected_result)


class TestCrew(unittest.TestCase):

    def setUp(self):
        self.oldfunc = p._crew_strings

        def fake_crew_strings(_):
            return self.test_crew_strings
        p._crew_strings = fake_crew_strings

    def tearDown(self):
        p._crew_strings = self.oldfunc

    def test_standard(self):
        self.test_crew_strings = [
            '09/04/2019 All               FO>FD HUTTON STUART       '
            + 'PU> WELCH FIONA         FA> CALLACHAN MICHAEL   '
            + 'FA> HAWKINGS KERRIN     FA> LUCAS BETHANY      ',
            '                             FA> LINE EXTRA',
            '10/04/2019 569,570,6253,6254 FO> VINCENT RICHARD     '
            + 'PU> SIMS GEORGIA        FA> DOUGLAS AYSHA       '
            + 'FA> KIMBERLEY CHRISTOPH FA> VINCENT  LORNA     ',
            '10/04/2019 *6253             CP> RIDLEY LEON SR     ',
            '10/04/2019 *6254             PU> PEACEY EMMA        ',
            '11/04/2019 All               FO> VINCENT RICHARD     '
            + 'PU> SHARRATT CHRISTOPHE FA> KIMBERLEY CHRISTOPH '
            + 'FA> LEWIS ANNA          FA> MADDEN CHLOE       ',
        ]
        duties = [
            p.Duty(
                DT(2019, 4, 9, 15, 30), DT(2019, 4, 9, 22, 33),
                (
                    p.Sector('6073', 'BRS', 'ALC',
                             DT(2019, 4, 9, 16, 27), DT(2019, 4, 9, 18, 55),
                             []),
                    p.Sector('6074', 'ALC', 'BRS',
                             DT(2019, 4, 9, 19, 37), DT(2019, 4, 9, 22, 3),
                             [],))),
            p.Duty(
                DT(2019, 4, 10, 11, 45), DT(2019, 4, 10, 22, 6),
                (
                    p.Sector('6253', 'BRS', 'LIS',
                             DT(2019, 4, 10, 13, 11), DT(2019, 4, 10, 15, 28),
                             []),
                    p.Sector('6254', 'LIS', 'BRS',
                             DT(2019, 4, 10, 16, 17), DT(2019, 4, 10, 18, 45),
                             []),
                    p.Sector('570', 'BRS', 'NCL',
                             DT(2019, 4, 10, 19, 12), DT(2019, 4, 10, 20, 13),
                             []),
                    p.Sector('569', 'NCL', 'BRS',
                             DT(2019, 4, 10, 20, 38), DT(2019, 4, 10, 21, 36),
                             []))),
            p.Duty(
                DT(2019, 4, 11, 11, 20), DT(2019, 4, 11, 22, 20),
                (
                    p.Sector('6241', 'BRS', 'BIO',
                             DT(2019, 4, 11, 12, 15), DT(2019, 4, 11, 13, 54),
                             []),
                    p.Sector('6242', 'BIO', 'BRS',
                             DT(2019, 4, 11, 14, 46), DT(2019, 4, 11, 16, 22),
                             []),
                    p.Sector('6035', 'BRS', 'MAD',
                             DT(2019, 4, 11, 17, 0), DT(2019, 4, 11, 19, 6),
                             []),
                    p.Sector('6036', 'MAD', 'BRS',
                             DT(2019, 4, 11, 19, 44), DT(2019, 4, 11, 21, 50),
                             [])))
        ]
        expected_results = {
            '201904096073~': (p.CrewMember("HUTTON STUART", "FO"),
                              p.CrewMember("WELCH FIONA", "PU"),
                              p.CrewMember("CALLACHAN MICHAEL", "FA"),
                              p.CrewMember("HAWKINGS KERRIN", "FA"),
                              p.CrewMember("LUCAS BETHANY", "FA"),
                              p.CrewMember("LINE EXTRA", "FA")),
            '201904096074~': (p.CrewMember("HUTTON STUART", "FO"),
                              p.CrewMember("WELCH FIONA", "PU"),
                              p.CrewMember("CALLACHAN MICHAEL", "FA"),
                              p.CrewMember("HAWKINGS KERRIN", "FA"),
                              p.CrewMember("LUCAS BETHANY", "FA"),
                              p.CrewMember("LINE EXTRA", "FA")),
            '20190410569~': (p.CrewMember("VINCENT RICHARD", "FO"),
                             p.CrewMember("SIMS GEORGIA", "PU"),
                             p.CrewMember("DOUGLAS AYSHA", "FA"),
                             p.CrewMember("KIMBERLEY CHRISTOPH", "FA"),
                             p.CrewMember("VINCENT LORNA", "FA")),
            '20190410570~': (p.CrewMember("VINCENT RICHARD", "FO"),
                             p.CrewMember("SIMS GEORGIA", "PU"),
                             p.CrewMember("DOUGLAS AYSHA", "FA"),
                             p.CrewMember("KIMBERLEY CHRISTOPH", "FA"),
                             p.CrewMember("VINCENT LORNA", "FA")),
            '201904106253~': (p.CrewMember("VINCENT RICHARD", "FO"),
                              p.CrewMember("SIMS GEORGIA", "PU"),
                              p.CrewMember("DOUGLAS AYSHA", "FA"),
                              p.CrewMember("KIMBERLEY CHRISTOPH", "FA"),
                              p.CrewMember("VINCENT LORNA", "FA")),
            '201904106254~': (p.CrewMember("VINCENT RICHARD", "FO"),
                              p.CrewMember("SIMS GEORGIA", "PU"),
                              p.CrewMember("DOUGLAS AYSHA", "FA"),
                              p.CrewMember("KIMBERLEY CHRISTOPH", "FA"),
                              p.CrewMember("VINCENT LORNA", "FA")),
            '20190410*6253~': (p.CrewMember("RIDLEY LEON SR", "CP"),),
            '20190410*6254~': (p.CrewMember("PEACEY EMMA", "PU"),),
            '201904116241~': (p.CrewMember("VINCENT RICHARD", "FO"),
                              p.CrewMember("SHARRATT CHRISTOPHE", "PU"),
                              p.CrewMember("KIMBERLEY CHRISTOPH", "FA"),
                              p.CrewMember("LEWIS ANNA", "FA"),
                              p.CrewMember("MADDEN CHLOE", "FA")),
            '201904116242~': (p.CrewMember("VINCENT RICHARD", "FO"),
                              p.CrewMember("SHARRATT CHRISTOPHE", "PU"),
                              p.CrewMember("KIMBERLEY CHRISTOPH", "FA"),
                              p.CrewMember("LEWIS ANNA", "FA"),
                              p.CrewMember("MADDEN CHLOE", "FA")),
            '201904116035~': (p.CrewMember("VINCENT RICHARD", "FO"),
                              p.CrewMember("SHARRATT CHRISTOPHE", "PU"),
                              p.CrewMember("KIMBERLEY CHRISTOPH", "FA"),
                              p.CrewMember("LEWIS ANNA", "FA"),
                              p.CrewMember("MADDEN CHLOE", "FA")),
            '201904116036~': (p.CrewMember("VINCENT RICHARD", "FO"),
                              p.CrewMember("SHARRATT CHRISTOPHE", "PU"),
                              p.CrewMember("KIMBERLEY CHRISTOPH", "FA"),
                              p.CrewMember("LEWIS ANNA", "FA"),
                              p.CrewMember("MADDEN CHLOE", "FA"))
        }
        self.assertEqual(p.crew("", duties), expected_results)

    # def test_no_crewtable_or_duties(self):
    #     self.test_crew_strings = []
    #     self.assertEqual(p.crew("", []), {})

    # def test_bad_crewstrings(self):
    #     self.test_crew_strings = ['10/04/2019 569,570,6253,6254 FO>']
    #     with self.assertRaises(p.CrewFormatException):
    #         p.crew("", [])
    #     self.test_crew_strings = ['09/04/2019 FO> HUTTON STUART']
    #     with self.assertRaises(p.CrewFormatException):
    #         p.crew("", [])
    #     self.test_crew_strings = ['31/11/2019 All   FO> HUTTON STUART']
    #     with self.assertRaises(p.CrewFormatException):
    #         p.crew("", [])
