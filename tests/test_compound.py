import unittest
from freezegun import freeze_time
import glob

import aims.parse
import aims.output
from aims.data_structures import InputFileException


@freeze_time("2024-01-01")
class Test_compound(unittest.TestCase):

    def test_compound(self):
        for f in glob.glob("files/*.htm"):
            with open(f) as input_:
                duties, ade = aims.parse.parse(input_.read())
            with open(f + ".txt") as roster_file:
                self.assertEqual(roster_file.read(),
                                 aims.output.roster(duties) + "\n")
            with open(f + ".ical", "rb") as ical_file:
                self.assertEqual(
                    ical_file.read(),
                    (aims.output.ical(duties, ade) + "\n").encode())
            with open(f + ".csv", "rb") as csv_file:
                self.assertEqual(csv_file.read(),
                                 (aims.output.csv(duties) + "\n").encode())
            with open(f + ".efj") as efj_file:
                self.assertEqual(efj_file.read(),
                                 aims.output.efj(duties) + "\n")

    def test_bad_file(self):
        with open("files/README") as f:
            with self.assertRaises(InputFileException):
                aims.parse.parse(f.read())
