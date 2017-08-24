import logging

from twitter import Status
from numpy.random import shuffle
from preppy.misc import (
    read_json,
    write_json,
    CodeBook
)


CODE_BOOK = CodeBook.from_json()


class TweetList(object):
    """
    Class object for constructing a tweet container
    has methods for adding a tweet only if it is
    not present, and writing files.
    """

    def __init__(self, tweets=None, metadata=None):
        """
        Return an instance of the TweetList class
        :param tweets: dict
            {'tweet_id_01': {tweet dict},
             'tweet_id_02': {tweet dict},...}
        :param metadata: dict
            {'tweet_id_01': {metadata dict},...}
        """
        if tweets is None:
            self.tweets = {}
        else:
            self.tweets = {id_str: Status(**tweet_dict)
                           for id_str, tweet_dict
                           in tweets.items()}
        if metadata is None:
            self._metadata = {}
        else:
            # TODO: Add mistake proofing
            self._metadata = metadata

    def __getitem__(self, i):
        try:
            return self.tweets[i]
        except KeyError:
            raise KeyError("Key {:} not found in TweetList".format(i))

    def __repr__(self):
        return str(self.as_dict)

    def __len__(self):
        return self.n

    @classmethod
    def from_session_file(cls, path=None):
        """
        Instantiate this class using a session file
        Format 1:
            Session files are JSON files whose primary
            key is tweet id string and whose value is
            a dict representation of a tweet
        Format 2:
            Session file contains two primary keys: ("metadata", "tweets")
            The "tweets" value is a dict in Format 1
            The "metadata" value is a dict of metadata
        :param path: path to a valid json file
        :return: An instance of this class
        """
        if path is None:
            path = "preppy_session.json"
        _d = read_json(path)
        if _d is not None:
            if "metadata" in _d.keys() and len(_d.keys()) == 2:
                return cls(_d["tweets"], _d["metadata"])
            elif len(_d.keys()) > 2:
                return cls(_d)
            else:
                raise IOError("Unable to parse session file")
        else:
            return cls()

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
        output_tweets = {
            k: v.AsDict()
            for k, v
            in self.tweets.items()
        }
        output = {"tweets": output_tweets,
                  "metadata": self._metadata}
        return output

    def as_list(self, only_geo=False, randomize=False):
        """
        Return the tweets as a list
        :param BoolType only_geo: If true, only
            return tweets which have a place
            attribute
        :param BoolType randomize:
            If true, shuffle the tweets randomly
        :return: list of twitter.Status objects
        """
        output = list(self.tweets.values())
        output.sort(key=lambda _tweet: _tweet.id)
        if only_geo:
            _output = []
            for tweet in output:
                if hasattr(tweet, "place"):
                    _output.append(tweet)
            output = _output
        if randomize:
            shuffle(output)
        return output

    @property
    def n(self):
        return len(self.tweets)

    @property
    def n_geotagged(self):
        return len(self.geotagged())

    def geotagged(self, tweet_format="Status", as_list=False):
        """
        Return a collection of the tweets that have geotags
        :param str tweet_format: format specifier for the tweets
        :param BoolType as_list:
            If True, return a list of tweets.
            Else return a dict of tweets.
        :return: list or dict (depends on as_list argument)
        """
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
        if as_list is True:
            keys = list(geo_tweets.keys())
            geo_tweets = [geo_tweets[key] for key in sorted(keys)]
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

    def add_tweets(self, tweets):
        """
        Add a list of tweets to the tweet list
        :param tweets: list or dict of tweets
            If dict, key is id string (id_str attribute)
        :return: List of ID strings that were added
        """
        if isinstance(tweets, (list, tuple)):
            tweet_dict = {tweet.id_str: tweet
                          for tweet in tweets}
        elif isinstance(tweets, dict):
            tweet_dict = tweets
        elif isinstance(tweets, TweetList):
            tweet_dict = tweets.tweets
        else:
            raise TypeError(
                'Cannot add tweet from {:}'
                .format(type(tweets))
            )
        self.tweets.update(tweet_dict)

    def user_has_encoded(self, user_id, variable_name, id_str):
        """
        State whether or not a given user has already
        encoded a given variable for a given tweet id
        :param user_id: the user ID string
        :param variable_name: the name of the variable
        :param id_str: the id of the tweet in question
        :return: BoolType
        """
        try:
            _ = self._metadata[id_str][variable_name][user_id]
            return True
        except KeyError:
            return False

    def get_metadata(self, id_str, param, user_id=None):
        """
        Get the metadata parameter value for a tweet
        :param id_str: the ID of the tweet
        :param param: the parameter name to be returned
        :param user_id: the user id associated with the
            value to be returned. If None, return the
            entire dict of all users who encoded that
            variable.
        :return: {str, dict, None}
        """
        output = None
        try:
            tweet_metadata = self._metadata[id_str]
        except KeyError:
            return output
        try:
            user_dict = tweet_metadata[param]
        except KeyError:
            return output
        if user_id is None:
            output = [
                float(val)
                for val
                in user_dict.values()
            ]
            # If user is not specified, return
            # an average value for the relevance
            return sum(output) / len(output)
        else:
            try:
                output = user_dict[user_id]
            except KeyError:
                return output
        return output

    def record_metadata(self, id_str, param, user_id, value):
        """
        Record a piece of metadata associated with a tweet
        Metadata dictionary is of the form:
        {
            $tweet_id_string$: {
                $param_name$: {
                    $user_id$: $param_value$
                }
            }
        }
        :param id_str: the id of the tweet
        :param param: the name of the variable to record
        :param user_id: the id of the user who encoded this variable
        :param value: the value of the variable to record
        """
        assert id_str in self.tweets
        if id_str not in self._metadata:
            self._metadata[id_str] = {}
        if param not in self._metadata[id_str]:
            self._metadata[id_str][param] = {}
        possible_values = CODE_BOOK.possible_values(param)
        if value in possible_values:
            self._metadata[id_str][param].update({user_id: value})
        else:
            logging.warning("Attempt was made to insert "
                            "\'{:}\' into param: \'{:}\'"
                            .format(value, param))

    def tweets_coded(self, variable_name):
        """
        Tell how many tweets have been coded for a given variable
        :param variable_name: The name of the variable in question
        :return: integer; how many tweets have had this variable coded
        """
        variable_name = variable_name.upper()
        if variable_name not in CODE_BOOK.__dict__:
            raise ValueError("{:} is not in the Code Book"
                             .format(variable_name))
        n = 0
        for id_str, var_dict in self._metadata.items():
            if variable_name in var_dict:
                n += 1
        return n

    def tweets_coding_status(self):
        """
        Print a status message describing how many
        tweets have been coded for each variable
        in the code book.
        :return: NoneType
        """
        n_tweets = self.n
        for var_name in CODE_BOOK.variable_names:
            n_coded = self.tweets_coded(var_name)
            print("{:} out of {:} tweets have been coded for {:}"
                  .format(n_coded, n_tweets, var_name.title()))

