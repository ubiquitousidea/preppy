import logging

from numpy.random import shuffle
from preppy.preptweet import PrepTweet
from preppy.misc import (
    read_json,
    write_json,
    CodeBook
)
from preppy.tweet_properties import is_relevant, has_geotag


CODE_BOOK = CodeBook.from_json()


class TweetList(object):
    """
    Class object for constructing a tweet container
    has methods for adding a tweet only if it is
    not present, and writing files.
    """

    def __init__(self, tweets=None):
        """
        Return an instance of the TweetList class
        this populates the tweets attribute with a dict of PrepTweet objects
        :param tweets: dict
            {'tweet_id_01': {tweet dict},
             'tweet_id_02': {tweet dict},...}
        """
        self.tweets = {
            id_str: PrepTweet.from_dict(pt_dict)
            for id_str, pt_dict
            in tweets.items()
        }

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

        Format I:
        {
            id_str: {
                tweet dict
            },...
        }

        Format II:
        {
            "metadata": {
                id_str: {
                    metadata_dict
                },...
            },
            "tweets": {
                id_str: {
                    tweet_dict
                },...
            }
        }

        Format III (best yet!):
        {
            id_str: {
                "status": {tweet dict},
                "metadata": {metadata dict}
            },...
        }
        :param path: path to a valid json file
        :return: An instance of this class
        """
        if path is None:
            path = "preppy_session.json"
        _d = read_json(path)
        if _d is not None:
            fmt = cls.detect_format(_d)
            if fmt == 1:
                raise NotImplementedError("Instantiation from format I session files not yet supported")
            elif fmt == 2:
                raise NotImplementedError("Instantiation from format II session files not yet supported")
            elif fmt == 3:
                return cls(_d)
            else:
                raise IOError("Unable to parse session file")
        else:
            return cls()

    @staticmethod
    def detect_format(_d):
        """
        Detect the format of a dictionary read from a session file
        For format spec, see from_session_file() classmethod
        :param _d: dictionary produced by reading json session file
        :return: integer
        """
        # TODO: detect the format of the dict
        return 2

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
        # in the following dict comprehension,
        # each v will be a PrepTweet instance
        output = {
            k: v.as_dict
            for k, v
            in self.tweets.items()
        }
        return output

    @property
    def relevant(self):
        """
        Return the tweets that have been coded as relevant
        as a list
        :return: list of PrepTweet instances
        """
        output = [tweet for tweet in self.tweets.values()
                  if is_relevant(tweet, self) == 1]
        output.sort(key=lambda _tweet: _tweet.id)
        return output

    @property
    def irrelevant(self):
        """
        Return the tweets that have been coded as irrelevant
        as a list
        :return: list of PrepTweet instances
        """
        output = [tweet for tweet in self.tweets.values()
                  if is_relevant(tweet, self) == 0]
        output.sort(key=lambda _tweet: _tweet.id)
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
        if only_geo:
            output = [tweet
                      for tweet
                      in self.tweets.values()
                      if has_geotag(tweet)]
        else:
            output = [tweet
                      for tweet
                      in self.tweets.values()]
        output.sort(key=lambda _tweet: _tweet.id)
        if randomize:
            shuffle(output)
        return output

    @property
    def n(self):
        return len(self.tweets)

    @property
    def n_geotagged(self):
        return len(self.geotagged())

    def geotagged(self, tweet_format="Status"):
        """
        Return a collection of the tweets that have geotags
        :param str tweet_format: format specifier for the tweets
        :return: list or dict (depends on as_list argument)
        """
        if tweet_format == "Status":
            def fn(_tweet):
                return _tweet
        elif tweet_format == "dict":
            def fn(_tweet):
                return _tweet.AsDict()
        else:
            msg = 'Tweet format can be \'dict\' or \'Status\''
            raise ValueError(msg)
        geo_tweets = {id_str: fn(tweet)
                      for id_str, tweet
                      in self.tweets.items()
                      if has_geotag(tweet)}
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
            average value for all users.
        :return: {str, dict, None} None is default
        """
        output = None
        assert isinstance(id_str, str)
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

    def clear_metadata(self, id_str, param=None):
        """
        Clear the metadata for a given tweet
        :param id_str: the tweet ID string
        :param param: name of the parameter to clear
            If None, all parameters will be cleared
        :return: NoneType
        """
        assert param in CODE_BOOK.variable_names
        if param is None:
            self._metadata[id_str] = {}
        else:
            self._metadata[id_str][param] = {}

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

    def predict_metadata(self, id_str, var_name):
        """
        Predict the value for a given variable
        Using KNN classification
        :param id_str: the id string of the tweet
        :param var_name: the name of the variable to be predicted
        :return: The predicted value for that variable
        """
        pass

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

