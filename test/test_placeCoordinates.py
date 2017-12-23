from unittest import TestCase
from preppy import PlaceInfo


class TestPlaceCoordinates(TestCase):
    def test_get_coordinates(self):
        """
        Test to see that the google geocoding api is working
        This test makes one API call to the Google Geocoding endpoint
        :return: None
        """
        pc = PlaceInfo(config_file="./config.json")
        place = "24 Hillhouse Ave, New Haven, CT, USA"
        coords = pc.get_coordinates(place)
        self.assertIsNotNone(coords)
        for x1, x2 in zip(coords, pc.get_coordinates(place)):
            self.assertEqual(x1, x2)
