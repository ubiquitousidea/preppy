"""
Initially, a twitter listener to determine the magnitude and location of public
discussion of PrEP (Truvada) on Twitter.

Future work may include expansion to other social media API"s and other health
topics. This will ultimately be the backend code used on a web based graphical
user interface to ask questions relevant to HIV researchers. Python chosen as
the language because of the Tornado and Scikit-Learn packages.
"""

import os
from twitter import Status
from numpy.random import choice
from numpy import array, zeros
from pandas import DataFrame
from .misc import (
    get_api, read_json, write_json,
    backup_session, make_list,
    SESSION_FILE_NAME, cull_old_files
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
        self.api = get_api(config_file)

    @property
    def as_dict(self):
        """
        Method for returning the contents of this object as a dictionary
        :return:
        """
        output = self.tweets.as_dict
        return output

    def status_prior(self, _term):
        print("There are {:d} tweets. Retrieving more tweets related to {:}".format(self.tweets.n, _term))

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
        len1 = len(self.tweets)
        self.tweets.add_tweets(tweetlist)
        len2 = len(self.tweets)
        return len2 - len1

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
        cull_old_files(self.backups_dir)


class TweetList(object):
    """
    Class object for constructing a tweet container
    has methods for adding a tweet only if it is
    not present, and writing files.
    """

    def __init__(self, tweets=None):
        """
        Return an instance of the TweetList class
        :param tweets: dict
            {'tweet_id_01': {tweet dict},
             'tweet_id_02': {tweet dict},...}
        """
        if tweets is None:
            self.tweets = {}
        else:
            self.tweets = {id_str: Status.NewFromJsonDict(tweet)
                           for id_str, tweet
                           in tweets.items()}
        self._metadata = {}

    def __getitem__(self, i):
        try:
            return self.tweets[i]
        except KeyError:
            raise KeyError("Key {:} not found in TweetList".format(i))

    def __repr__(self):
        return str(self.as_dict)

    def __len__(self):
        return self.n

    # def __iter__(self):

    @classmethod
    def from_session_file(
            cls, path=None):
        """
        Instantiate this class using a session file
        Format 1:
            Session files are JSON files whose primary
            key is tweet id string and whose value is
            a dict representation of a tweet
        :param path: path to a valid json file
        :return: An instance of this class
        """
        if path is None:
            path = SESSION_FILE_NAME
        _d = read_json(path)
        if _d:
            return cls(_d)

    @property
    def id_list(self):
        ids = list(self.tweets.keys())
        ids.sort()
        return ids

    @property
    def id_list_geo(self):
        ids = list(self.geotagged().keys())
        ids.sort()
        return ids

    @property
    def as_dict(self):
        """
        Property to return json representation of this class instance
        The self.tweets is a dict of <twitter.models.Status> objects
        This method converts the Status objects to dictionaries
        :return: dict of dict representations of tweets (Statuses)
        """
        return {k: v.AsDict()
                for k, v
                in self.tweets.items()}

    @property
    def n(self):
        return len(self.tweets)

    @property
    def n_geotagged(self):
        return len(self.geotagged())

    def geotagged(self, tweet_format="Status"):
        valid_formats = ("Status", "dict")
        assert tweet_format in valid_formats
        if tweet_format == "Status":
            def fn(_tweet):
                return _tweet
        elif tweet_format == "dict":
            def fn(_tweet):
                return _tweet.AsDict()
        geo_tweets = {id_str: fn(tweet)
                      for id_str, tweet
                      in self.tweets.items()
                      if "place" in tweet.AsDict()}
        return geo_tweets

    def export_geotagged_tweets(self, path=None):
        if path is None:
            path = "geotagged_tweets.json"
        d = self.geotagged(tweet_format="dict")
        write_json(d, path)

    @property
    def max_id(self):
        ids = [int(i) for i in self.id_list]
        if ids:
            max_id = max(ids)
        else:
            max_id = None
        return max_id

    @property
    def min_id(self):
        ids = [int(i) for i in self.id_list]
        if ids:
            min_id = min(ids)
        else:
            min_id = None
        return min_id

    def add_tweet(self, tweet):
        """
        Try adding a single tweet to the tweet list
        This uses the dict.update method which will
        overwrite any preexisting tweet of the same
        id (unique identifier string)
        :param twitter.Status tweet: A tweet
        :return: How many tweets were added. integer.
        """
        id_str = tweet.id_str
        if id_str not in self.tweets:
            self.tweets[id_str] = tweet
            return 1
        else:
            return 0

    def add_tweets(self, tweets):
        """
        Add a list of tweets to the tweet list
        :param tweets: list or dict of tweets
            If dict, key is id string (id_str attribute)
        :return: List of ID strings that were added
        """
        id_list = []
        n_added = 0
        if type(tweets) is list:
            for tweet in tweets:
                id_list.append(tweet.id_str)
                n_added += self.add_tweet(tweet)
        elif type(tweets) is dict:
            for id_str, tweet in tweets.items():
                id_list.append(id_str)
                n_added += self.add_tweet(tweet)
        elif type(tweets) is TweetList:
            self.add_tweets(tweets.tweets)
        return id_list

    def record_metadata(self, id_str, param, value):
        """
        Record a piece of metadata associated with a tweet
            Example of metadata parameter could be:
                is_related_to_prep
                is_related_to_truvada
        :param id_str: the id of the tweet
        :param param: the name of the parameter to record
        :param value: the value of the parameter to record
        """
        assert id_str in self.tweets
        if id_str not in self._metadata:
            self._metadata[id_str] = {}
        self._metadata[id_str].update({param: value})


class ReportWriter(object):
    def __init__(self, tweets):
        """
        Instantiate a ReportWriter using a TweetList
        :param tweets:
        """
        assert isinstance(tweets, TweetList)
        self.tweets = tweets

    def how_many_geotagged(self):
        return self.tweets.n_geotagged

    @property
    def geotagged(self):
        """
        Returns a dictionary of tweets that
        contain a 'place' attribute
        :return: dict of twitter.Status objects
        """
        return self.tweets.geotagged()

    @property
    def table_all(self):
        tweets = list(self.tweets.tweets.values())
        tweets.sort(key=lambda tweet: tweet.id)
        return self.make_table(tweets)

    @property
    def table_geo(self):
        """
        Return a table of geotagged tweets with columns:
            0: tweet ID string
            1: state
            2: tweet text
            3: state political affiliation
        :return: pandas.DataFrame
        """
        tweets = list(self.geotagged.values())
        tweets.sort(key=lambda tweet: tweet.id)
        return self.make_table(tweets)

    def country_counts(self, min_count=3):
        table = self.table_geo
        counts = table.country.value_counts()
        if min_count > 0:
            counts = counts[counts >= min_count]
        return counts

    @staticmethod
    def make_table(tweets):
        """
        Return a pandas.DataFrame table of tweet information
        :param tweets: list of Tweets (twitter.Status instances)
        :return: pandas.DataFrame
        """
        missing = None
        valid_state_codes = read_json(
            "{:}/state_codes.json".format(os.path.dirname(__file__)))\
            ["valid_state_codes"]

        def get_id(tweet):
            return tweet.id

        def get_date(tweet):
            return tweet.created_at

        def get_user_id(tweet):
            try:
                return tweet.user.id
            except:
                return missing

        def get_text(tweet):
            try:
                if tweet.full_text:
                    return tweet.full_text
                elif tweet.text:
                    return tweet.text
                else:
                    return missing
            except:
                return missing

        def get_place(tweet):
            try:
                return tweet.place["full_name"]
            except:
                return missing

        def get_centroid(tweet):
            try:
                bounding_box = array(
                    tweet.place
                    ["bounding_box"]
                    ["coordinates"]
                    ).squeeze()
                centroid = bounding_box.mean(axis=0)
                return centroid
            except:
                return zeros(2)

        def get_longitude(tweet):
            try:
                centroid = get_centroid(tweet)
                return centroid[0]
            except:
                return missing

        def get_latitude(tweet):
            try:
                centroid = get_centroid(tweet)
                return centroid[1]
            except:
                return missing

        def get_country(tweet):
            assert isinstance(tweet, Status)
            try:
                return tweet.place["country"]
            except:
                return missing

        def get_state(tweet):
            """
            Get the state in which the tweet originated
            Currently relies upon the JSON response from twitter API
            Consider future use of Google reverse geocoding API

            Information page:
            https://developers.google.com/maps/documentation/geocoding/start

            Example:
            https://maps.googleapis.com/maps/api/geocode/json?latlng=40.714224,-73.961452&key=...

            :param tweet:
            :return:
            """
            assert isinstance(tweet, Status)
            state_code = missing
            country_code = tweet.place["country_code"]
            place_type = tweet.place["place_type"]
            if country_code == "US" and place_type == "city":
                full_name = tweet.place["full_name"]
                state_code = full_name.split(",")[-1].strip().upper()
                state_code = state_code if state_code in valid_state_codes else missing
            else:
                pass
            return state_code



        column_getters = (
            ("id", get_id),
            ("date", get_date),
            ("user", get_user_id),
            ("text", get_text),
            ("place", get_place),
            ("country", get_country),
            ("longitude", get_longitude),
            ("latitude", get_latitude),
            ("state", get_state)
        )
        output_dict = {
            key: [
                fn(tweet)
                for tweet
                in tweets
            ]
            for key, fn
            in column_getters
        }
        return DataFrame.from_dict(output_dict)

    def write_report_geo(self, path):
        report = self.table_geo
        report.to_csv(path)

    def get_random_tweet(self):
        id_str = choice(self.tweets.id_list)
        return self.tweets[id_str]

    def get_random_geo_tweet(self):
        id_str = choice(self.tweets.id_list_geo)
        return self.tweets[id_str]
