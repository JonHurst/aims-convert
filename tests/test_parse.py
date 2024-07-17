import unittest

from aims.parse import parse
from aims.data_structures import InputFileException


class TestParse(unittest.TestCase):

    def test_empty(self):
        with self.assertRaises(InputFileException):
            parse("")

    def test_bad(self):
        with self.assertRaises(InputFileException):
            parse("afjp oijfqoefqnknzn a")

    def test_wrong_html(self):
        with self.assertRaises(InputFileException):
            parse("<!DOCTYPE html><html><head><title>Bad</title></head>"
                  "<body><p>Bad!</p></body></html>")
