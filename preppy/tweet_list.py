from twitter import Status
from numpy.random import shuffle
from preppy.preptweet import PrepTweet
from preppy.metadata import MetaData, CODE_BOOK
from preppy.misc import read_json, write_json, get_logger


logger = get_logger(__file__)


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
        } if tweets is not None else {}

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
        return 3

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
                  if tweet.relevance == 1]
        output.sort(key=lambda _tweet: _tweet.id)
        return output

    def get_keyword_relevant(self, sample_size=None, randomize=False):
        """
        Return a list of tweets that keyword_classify.R coded as relevant
        and have not yet been run through watson
        :param sample_size: number of tweets to return
        :param randomize: uses numpy.random.shuffle
        :return: list of PrepTweet instances
        """
        output = [tweet for tweet in self.tweets.values()
                  if tweet.keyword_relevant]
        if randomize:
            shuffle(output)
        if sample_size:
            output = output[:sample_size]
        return output

    @property
    def irrelevant(self):
        """
        Return the tweets that have been coded as irrelevant
        as a list
        :return: list of PrepTweet instances
        """
        output = [tweet for tweet in self.tweets.values()
                  if tweet.relevance == 0]
        output.sort(key=lambda _tweet: _tweet.id)
        return output

    def as_list(self, only_geo=False, randomize=False, coded_for=None):
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
                      if tweet.has_geotag]
        else:
            output = list(self.tweets.values())
        if coded_for is not None:
            output = [tweet for tweet
                      in output if tweet.has_been_coded_for(coded_for)]
        if randomize:
            shuffle(output)
        else:
            output.sort(key=lambda _tweet: _tweet.id)
        return output

    @property
    def n(self):
        return len(self.tweets)

    @property
    def n_geotagged(self):
        """
        The number of tweets that are geotagged
        """
        return len(self.geotagged())

    def geotagged(self, tweet_format="Status"):
        """
        Return a collection of the tweets that have geotags
        :param str tweet_format: format specifier for the tweets
        :return: dict
        """
        if tweet_format == "Status":
            def fn(_tweet):
                return _tweet
        elif tweet_format == "dict":
            def fn(_tweet):
                return _tweet.as_dict
        else:
            msg = 'Tweet format can be \'dict\' or \'Status\''
            raise ValueError(msg)
        geo_tweets = {id_str: fn(tweet)
                      for id_str, tweet
                      in self.tweets.items()
                      if tweet.has_geotag}
        return geo_tweets

    def export_geotagged_tweets(self, path=None):
        """
        Write the geotagged tweets to a JSON file.
        :param path: path to the file. If None, default will be used.
        :return: NoneType
        """
        if path is None:
            path = "geotagged_tweets.json"
        d = self.geotagged(tweet_format="dict")
        write_json(d, path)

    @property
    def max_id(self):
        """
        The largest Tweet ID present in this collection of tweets
        This corresponds to the newest tweet.
        :return: int
        """
        ids = [int(i) for i in self.id_list]
        if ids:
            max_id = max(ids)
        else:
            max_id = None
        return max_id

    @property
    def min_id(self):
        """
        The smallest Tweet ID present in this collection of tweets
        This correspond to the oldest tweet.
        :return: int
        """
        ids = [int(i) for i in self.id_list]
        if ids:
            min_id = min(ids)
        else:
            min_id = None
        return min_id

    def add_tweets(self, tweets):
        """
        Add tweets to this TweetList
        This method tries to be very accommodating with the
        types of arguments that it can handle.
        :param tweets: list, dict or TweetList object
            Contents of this object should be Status, PrepTweet, or dict objects.
        :return: NoneType
        """

        def accommodate_format(_tweet):
            """
            local function to ensure that the argument passed
            in is returned as a PrepTweet object
            :param _tweet: dict, Status, or PrepTweet
            :return: PrepTweet
            """
            if isinstance(_tweet, (Status, dict)):
                return PrepTweet(_tweet)
            elif isinstance(_tweet, PrepTweet):
                return _tweet

        if isinstance(tweets, TweetList):
            tweet_dict = tweets.tweets
        elif isinstance(tweets, (list, tuple)):
            tweet_dict = {tweet.id_str: accommodate_format(tweet)
                          for tweet in tweets}
        elif isinstance(tweets, dict):
            tweet_dict = {tweet.id_str: accommodate_format(tweet)
                          for id_str, tweet in tweets.items()}
        else:
            raise TypeError("Unable to add tweets from {}".format(type(tweets)))
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
            value = self.get_metadata_value(id_str, variable_name, user_id)
            return value is not None
        except AttributeError:
            return False

    def get_metadata_obj(self, id_str):
        """
        Return the metadata object a given tweet
        :param id_str: the ID string of that tweet
        :return:
        """
        try:
            tweet = self.tweets[id_str]
            return tweet.metadata
        except KeyError:
            logger.warning("Tweet id {} does not exist in the tweet list".format(id_str))
            return MetaData()  # empty metadata

    def get_metadata_value(self, id_str, param, user_id=None):
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
            tweet_metadata = self.tweets.get(id_str).get("metadata")
        except KeyError:
            return output
        try:
            user_dict = getattr(tweet_metadata, param)
        except AttributeError:
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
            try:
                self.tweets[id_str].metadata = MetaData()
            except:
                logger.warning("Did not clear metadata for tweet {}".format(id_str))
        else:
            try:
                pt = self.tweets.get(id_str)
                assert isinstance(pt, PrepTweet)
                md = pt.metadata
                assert isinstance(md, MetaData)
                setattr(md, param, {})
            except:
                logger.warning("Did not clear metadata for param {}, tweet {}".format(param, id_str))

    def record_metadata(self, id_str, param, user_id, value):
        """
        Record a piece of metadata associated with a tweet
        :param id_str: the id of the tweet
        :param param: the name of the variable to record
        :param user_id: the id of the user who encoded this variable
        :param value: the value of the variable to record
        """
        tweet = self.tweets.get(id_str)
        if tweet is not None:
            tweet.metadata.record(param, user_id, value)

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
        for preptweet in self.tweets.values():
            if preptweet.has_been_coded_for(variable_name):
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
            logger.info("{:} out of {:} tweets have been coded for {:}"
                  .format(n_coded, n_tweets, var_name.title()))

