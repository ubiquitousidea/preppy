from unittest import TestCase
from preppy import PlaceInfo


class TestPlaceCoordinates(TestCase):
    def test_get_coordinates(self):
        """
        Test to see that the google geocoding api is working
        This test makes one API call to the Google Geocoding endpoint
        :return: None
        """
        info = PlaceInfo(config_file="./config.json")
        place = "24 Hillhouse Ave, New Haven, CT, USA"
        coords = info.get_coordinates(place)
        self.assertIsNotNone(coords)
        for x1, x2 in zip(coords, info._get_coords_from_self(place)):
            self.assertEqual(x1, x2)

    def test_get_zip_code(self):
        """
        Test to see that we can get the zip code from a place
        :return: None
        """
        info = PlaceInfo(config_file="./config.json")
        place = "17 Hillhouse Ave. New Haven, CT, USA"
        zc = info.get_zip_code(place)
        self.assertTrue(zc == "06511")
