import requests

from preppy.misc import read_json, write_json, MISSING, get_logger


logger = get_logger(__file__)


class DataObject(object):
    """
    A base object for storing and manipulating data
    """
    def __init__(self, data=None, *args, **kwargs):
        self._data = {}
        self.data = data

    @classmethod
    def from_json(cls, fname, *args, **kwargs):
        """
        Instantiate this class from a json file
        :param fname: name of the json file that was
            written by an instance of this class
        :return: an instance of this class
        """
        d = read_json(fname)
        return cls(d, *args, **kwargs)

    def to_json(self, fname):
        """
        Write out the contents of this class as a json file
        :param fname: the name of the json file to write
        :return: None
        """
        write_json(self.data, fname)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, d):
        if d is not None:
            assert isinstance(d, dict)
            self._data = d


class PlaceInfo(DataObject):
    def __init__(self, data=None, config_file=None):
        """
        Initialize a PlaceCoordinates class object

        :param data: dictionary of the form
            {place : coords, ...}
        :param config_file: configuration file that
            contains the api key for the requests
        """
        DataObject.__init__(self)
        self.data = data
        self.api_key = None
        if config_file is not None:
            configuration = read_json(config_file)
            try:
                self.api_key = configuration["google"]["keys"]["api_key"]
            except KeyError:
                raise KeyError("Config json file must have key path google>keys>api_key. Google API not in use.")
        self.url_geocode_resource = "https://maps.googleapis.com/maps/api/geocode/json"
        self.api_counter = 0

    def get_coordinates(self, place_name):
        """
        Return the coordinates of a place
        :param place_name: the name of the place
        :return: tuple of floats (latitude, longitude)
        """
        if place_name in self.data:
            coords = self._get_coords_from_self(place_name)
        else:
            coords = self._get_coords_from_api(place_name)
        return coords

    def get_zip_code(self, place_name):
        """
        Get the US Zip code of a place
        :param place_name: the name of the place
        :return: string representation of the zip code
        """
        if place_name in self.data:
            zc = self._get_zip_code_from_self(place_name)
        else:
            zc = self._get_zip_code_from_api(place_name)
        return zc

    # ----------------------------------------------------------------
    # - Protected methods -
    # ----------------------------------------------------------------

    def _query_geocode_api(self, place_name):
        """
        This is the method that makes a call to the Google Geocoding API
        Store the resulting json dict in self.data
        return the results that were stored
        :param place_name: name of the place to search for
        :return: dict
            specifically: response.json()["results"][0]
        """
        response = requests.get(
            url=self.url_geocode_resource,
            params={
                "address": place_name,
                "key": self.api_key
            }
        )
        self.api_counter += 1
        results = self.store_results(place_name, response)
        return results

    def _get_coords_from_api(self, place_name):
        """
        Get the coordinates of a place from
            Google Geocoding API
        Store the API response in self.data
        Return the coordinates from that response
        :param place_name: name of the place
        :return: tuple of floats (latitude / longitude)
        """
        results = self._query_geocode_api(place_name)
        coords = self._get_coords_from_results(results)
        return coords

    def _get_zip_code_from_api(self, place_name):
        """
        Get zip code of a place from the Google Geocoding API
        :param place_name: name of a place
        :return: string representation of zip code
        """
        results = self._query_geocode_api(place_name)
        zc = self._get_zip_code_from_results(results)
        return zc

    def _get_coords_from_self(self, place_name):
        """
        Get the coordinates of a place from the cached responses
        :param place_name: name of the place (key in self.data)
        :return: tuple of floats (latitude, longitude)
        """
        results = self.data.get(place_name)
        return self._get_coords_from_results(results)

    def _get_zip_code_from_self(self, place_name):
        """
        Get the zip code of a place from the cached responses
        :param place_name: name of the place
        :return: string representation of the zip code
        """
        results = self.data.get(place_name)
        return self._get_zip_code_from_results(results)

    def store_results(self, place_name, response):
        """
        Store the results from a search in self.data
        :param place_name: name of the place
        :param response: http response object from google geocoding api
        :return: results dict (parsed from json response)
        """
        try:
            results_dict = response.json()['results'][0]
        except:
            results_dict = {}
        if place_name is not None:
            self.data.update({place_name: results_dict})
        return results_dict

    @staticmethod
    def _get_coords_from_results(d):
        """
        Get the coordinates of a place from the json response
            returned by Google Geocoding API.
        :param d: json response from the api. For example
            response = requests.get(url, params)
            d = response.json()['results'][0]
        :return: (latitude, longitude).  A tuple of floats
        """
        try:
            location_dict = d["geometry"]["location"]
            coords = location_dict.get("lat"), location_dict.get("lng")
            return coords
        except:
            return MISSING

    @staticmethod
    def _get_zip_code_from_results(d):
        """
        Extract the zip code information from a results dictionary
        :param d: dictionary of results from google
        :return: string repr of zip code
        """
        def is_zip_code(cmp):
            try:
                return "postal_code" in cmp["types"]
            except KeyError:
                return False
        try:
            iz = list(
                map(
                    is_zip_code,
                    d.get("address_components")
                )
            )
            zc = d.get("address_components")[iz.index(True)]["long_name"]
            return zc
        except:
            return MISSING