"""
The test suite (Unittest...)
"""

from bin.misc import date_string
import unittest


class Tester(unittest.TestCase):
    def setUp(self):
        pass

    def test_date_string(self):
        print(
            date_string()
        )
