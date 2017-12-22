from unittest import TestCase
from preppy import PlaceCoordinates


class TestPlaceCoordinates(TestCase):
    def test_get_coordinates(self):
        """
        Test to see that the google geocoding api is working
        :return: None
        """
        pc = PlaceCoordinates(config_file="./config.json")
        coords = pc.locate("Bangkok Thailand")
        self.assertIsNotNone(coords)
