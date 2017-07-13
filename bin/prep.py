"""
Initially, a twitter listener to determine the magnitude and location of public
discussion of PrEP (Truvada) on Twitter.

Future work may include expansion to other social media API"s and other health
topics. This will ultimately be the backend code used on a web based graphical
user interface to ask questions relevant to HIV researchers. Python chosen as
the language because of the Tornado and Scikit-Learn packages.
"""

import sys
from twitter.models import Status
from misc import (
    get_api, read_json, write_json, SESSION_FILE_NAME,
    cull_old_files, backup_session
)


TWEETS = "tweets"
IDLIST = "index_list"


class Preppy(object):
    def __init__(self, session_file_name=None,
                 try_default_session=True,
                 custom_backup_dir=None):
        """
        Return an instance of Preppy class
        :param str session_file_name: Name of a session file (optional)
        """
        if session_file_name:
            self.tweets = TweetList.from_session_file(session_file_name)
        elif try_default_session:
            self.tweets = TweetList.from_session_file("preppy_session.json")
        else:
            self.tweets = TweetList()
        self.backups_dir = custom_backup_dir if custom_backup_dir else "backups"
        self.api = get_api()

    @property
    def as_dict(self):
        """
        Method for returning the contents of this object as a dictionary
        :return:
        """
        output = self.tweets.as_dict
        return output

    def status_prior(self, _term):
        print("There are {:d} tweets. Retrieving more tweets related to {:s}".format(self.tweets.n, _term))

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

    def sequentially_search(self, term, lang='en',
                            last_session_backstop=False):
        """
        Sequentially search for term $term
        :param str term: search term
        :param str lang: Tweet language.
        :param BoolType last_session_backstop: If true, search
            only covers that which wasn't covered in previous run.
            Use False if starting a new keyword when previous
            session did not use that keyword.
        :return: NoneType. Modifies self.tweets in place
        """
        query = {"term": [term],
                 "count": 100,
                 "lang": lang,
                 "result_type": "recent"}
        if last_session_backstop:
            min_id = self.tweets.max_id
            if min_id is not None:
                query.update({"since_id": min_id})
        tweet_list = TweetList()
        i = 0
        max_iter = 180
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
        self.add_tweets(tweet_list)

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
        write_json(output, SESSION_FILE_NAME)
        return SESSION_FILE_NAME

    def cleanup_session(self):
        session_file_name = self.write_session_file()
        backup_session(self.backups_dir, session_file_name)
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
            self.tweets = {id_str: Status(**tweet)
                           for id_str, tweet
                           in tweets.items()}

    @classmethod
    def from_dict(cls, d):
        _obj = cls()
        _obj.tweets.update({k: Status(**v) for k, v in d.items()})
        return _obj

    @classmethod
    def from_session_file(cls, fname):
        d = read_json(fname)
        if d:
            return cls.from_dict(d)

    @property
    def as_dict(self):
        """
        Property to return json representation of this class
        The self.tweets is a dict of <twitter.models.Status> objects
        This method converts the Status objects to dictionaries
        :return: dict of dict representations of tweets (Statuses)
        """
        return {k: v.AsDict()
                for k, v
                in self.tweets.items()}

    def __repr__(self):
        return str(self.as_dict)

    def __len__(self):
        return self.n

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
            geo_tweets = {id_str: tweet
                          for id_str, tweet
                          in self.tweets.items()
                          if "place" in tweet.AsDict()}
        elif tweet_format == "dict":
            geo_tweets = {id_str: tweet.AsDict()
                          for id_str, tweet
                          in self.tweets.items()
                          if "place" in tweet.AsDict()}
        else:
            raise ValueError(
                "Format must be in {:s}".format(
                    valid_formats.__str__()))
        return geo_tweets

    def export_geotagged_tweets(self):
        d = self.geotagged(tweet_format="dict")
        write_json(d, "geotagged_tweets.json")

    @property
    def max_id(self):
        id_strings = list(self.tweets.keys())
        ids = [int(i) for i in id_strings]
        if ids:
            max_id = max(ids)
        else:
            max_id = None
        return max_id

    @property
    def min_id(self):
        id_strings = list(self.tweets.keys())
        ids = [int(i) for i in id_strings]
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


class ReportWriter(object):
    def __init__(self, preppy):
        assert isinstance(preppy, Preppy)
        self.p = preppy

    def how_many_geotagged(self):
        # Do this
        return self.p.tweets.n_geotagged



if __name__ == "__main__":
    try:
        d = read_json(sys.argv[1])
        termlist = d["TERMS"]
    except KeyError:
        termlist = ["Truvada"]
    Session = Preppy(try_default_session=True)
    for term in termlist:
        Session.get_more_tweets(term, lsb=False)
    Session.tweets.export_geotagged_tweets()
    Session.cleanup_session()
