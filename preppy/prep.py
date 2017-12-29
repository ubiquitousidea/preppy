"""
Initially, a twitter listener to determine the magnitude and location of public
discussion of PrEP (Truvada) on Twitter.

Future work may include expansion to other social media API"s and other health
topics. This will ultimately be the backend code used on a web based graphical
user interface to ask questions relevant to HIV researchers. Python chosen as
the language because of the Tornado and Scikit-Learn packages.
"""

import time
import logging
import requests
from numpy.random import shuffle
from getpass import getuser
from preppy.tweet_list import TweetList
from preppy.preptweet import PrepTweet, CODE_BOOK
from preppy.misc import (
    get_twitter_api, read_json, write_json,
    backup_session, make_list, cull_old_files,
    ask_param, CodeBook, MISSING, rehydrate_tweets
)


class Preppy(object):
    def __init__(self, session_file_path,
                 backup_dir=None,
                 config_file=None):
        """
        Return an instance of Preppy class
        :param str session_file_path: Name of a session file (optional)
        """
        self.session_file_path = session_file_path
        if session_file_path:
            self.tweets = TweetList.from_session_file(
                self.session_file_path)
        else:
            self.tweets = TweetList()
        self.backups_dir = backup_dir
        self.api = get_twitter_api(config_file)

    @property
    def as_dict(self):
        """
        Method for returning the contents of this object as a dictionary
        :return:
        """
        output = self.tweets.as_dict
        return output

    def status_prior(self, _term=None):
        """
        State how many tweets there are
        Optionally include a message about which term is going to be searched
        :param _term: Optional. Term being searched
        :return: NoneType
        """
        msg = "There are {:d} tweets.".format(self.tweets.n)
        if _term is not None:
            msg += "Retrieving more tweets related to {:}".format(_term)
        print(msg)

    def status_posterior(self):
        print("There are {:d} tweets now".format(self.tweets.n))
        print("Of those, {:d} are geo-tagged".format(self.tweets.n_geotagged))

    def get_tweets(self, term):
        """
        #--------------------------------------------------------- a landmark -
        # - Run preppy session initially --------------------------------------
        #----------------------------------------------------------------------
        Search for a term an get all available tweets. Use this first.
        :param term:
        :return:
        """
        self.get_more_tweets(term, lsb=False)

    def get_more_tweets(self, term, lsb=True):
        """
        #--------------------------------------------------- another landmark -
        # - Run preppy session after initial run ------------------------------
        #----------------------------------------------------------------------

        :param BoolType lsb: Last Session Backstop.
            See self.sequentially_search() docstring
        :return: NoneType
        """
        self.status_prior(term)
        self.sequentially_search(term, last_session_backstop=lsb)
        self.status_posterior()

    def sequentially_search(self, terms, lang='en',
                            last_session_backstop=False):
        """
        Sequentially search for term $term
        :param {tuple, list} terms: list of search terms
        :param str lang: Tweet language.
        :param BoolType last_session_backstop: If true, search
            only covers that which wasn't covered in previous run.
            Use False if starting a new keyword when previous
            session did not use that keyword.
        :return: NoneType. Modifies self.tweets in place
        """
        terms = make_list(terms)
        min_id = self.tweets.max_id \
            if last_session_backstop else None
        for term in terms:
            query = {
                "term": term,
                "count": 100,
                "lang": lang,
                "result_type": "recent"
            }
            if min_id is not None:
                query.update({"since_id": min_id})
            tweet_list = self.search_single_term(query)
            n_added = self.add_tweets(tweet_list)
            print("Added {:d} tweets related to {:}"
                  .format(n_added, term))

    def search_single_term(self, query):
        """
        Search using a query dictionary

        This method actually contains the
            twitter.Api.GetSearch call

        :param query: dictionary of search arguments
        :return: TweetList object
        """
        i = 0
        max_iter = 180
        tweet_list = TweetList()
        while i < max_iter:
            n1 = len(tweet_list)
            i += 1
            max_id = tweet_list.min_id
            if max_id is not None:
                query.update({
                    "max_id": str(max_id - 1)
                })
            response = self.api.GetSearch(**query)
            tweet_list.add_tweets(response)
            n2 = len(tweet_list)
            if n1 == n2:
                break
        return tweet_list

    def add_tweets(self, tweetlist):
        """
        Add tweets from a list or dict
        :param tweetlist: list or dict of twitter.Status instances
        :return: integer; Change in size of the tweet list
        """
        len1 = len(self.tweets)
        self.tweets.add_tweets(tweetlist)
        len2 = len(self.tweets)
        return len2 - len1

    def rehydrate_tweets(self):
        """
        Rehydrate tweets from web
        """
        id_list = self.tweets.id_list
        tweets_dict = rehydrate_tweets(id_list, self.api)
        tweets_added = len(tweets_dict)
        print("Rehydrated {:} tweets".format(tweets_added))
        self.add_tweets(tweets_dict)

    def encode_variable(self,
                        variable_name,
                        user_id=None,
                        only_geo=True,
                        max_tweets=100,
                        randomize=True):
        """
        User interaction.
        Ask user to encode a variable
        Record the value as an item of metadata
            in self._metadata
        :param variable_name: the name of the variable to encode
            (must be in CodeBook)
        :param {int, str} user_id: The identifier assigned
            to a user when performing this variable encoding
        :param BoolType only_geo: if True, only iterate
            through the tweets which are geotagged
        :param int max_tweets: How may tweets to encode before retiring
        :param randomize: If true, randomly select tweet order
        :return: NoneType. Modifies self._metadata in place.
        """
        variable_name = variable_name.upper()
        assert CODE_BOOK.has_variable(variable_name)
        user_id = getuser() if user_id is None else user_id
        possible_values = CODE_BOOK.possible_values(variable_name)
        tweets = self.tweets.as_list(only_geo, randomize)
        tweet_count = 0
        for tweet in tweets:
            assert isinstance(tweet, PrepTweet)
            if self.tweets.user_has_encoded(
                    user_id, variable_name, tweet.id_str):
                # If this user has already encoded that
                # variable, do not show the tweet again
                continue

            p_relevance = tweet.is_relevant

            if variable_name != "RELEVANCE" \
                    and p_relevance is not None \
                    and p_relevance < 0.5:
                # If encoding another variable other than
                # relevance, only show the tweet it is relevant
                continue

            param_val = MISSING
            max_iter = 10
            i = 0
            while i < max_iter:
                i += 1
                param_val = ask_param(
                    param_name=variable_name,
                    tweet=tweet,
                    api=self.api
                )
                if param_val in possible_values:
                    break
                else:
                    msg = "Possible values: {:}"
                    value = CODE_BOOK.explain_possible_values(variable_name)
                    print(msg.format(value))
            self.tweets.record_metadata(
                id_str=tweet.id_str,
                param=variable_name,
                user_id=user_id,
                value=param_val
            )
            tweet_count += 1
            if max_tweets != 0 and tweet_count >= max_tweets:
                break

    def write_session_file(self):
        """
        Write a json file of the current session
        :return: NoneType
        """
        output = self.as_dict
        write_json(output, self.session_file_path)

    def cleanup_session(self):
        self.write_session_file()
        backup_session(self.backups_dir, self.session_file_path)
        cull_old_files(self.backups_dir, n_keep=10)


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
        results_dict = response.json()['results'][0]
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
        location_dict = d["geometry"]["location"]
        return location_dict.get("lat"), location_dict.get("lng")

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

        iz = list(
            map(
                is_zip_code,
                d.get("address_components")
            )
        )
        zc = d.get("address_components")[iz.index(True)]["long_name"]
        return zc