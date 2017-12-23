from unittest import TestCase
from preppy import PlaceCoordinates


class TestPlaceCoordinates(TestCase):
    def test_get_coordinates(self):
        """
        Test to see that the google geocoding api is working
        This test makes one API call to the Google Geocoding endpoint
        :return: None
        """
        pc = PlaceCoordinates(config_file="./config.json")
        place = "Bangkok Thailand"
        coords = pc.locate(place)
        self.assertIsNotNone(coords)
        for x1, x2 in zip(coords, pc.data[place]):
            self.assertEqual(x1, x2)
