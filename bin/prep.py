"""
Initially, a twitter listener to determine the magnitude and location of public
discussion of PrEP (Truvada) on Twitter.

Future work may include expansion to other social media API"s and other health
topics. This will ultimately be the backend code used on a web based graphical
user interface to ask questions relevant to HIV researchers. Python chosen as
the language because of the Tornado and Scikit-Learn pacakges.
"""

from twitter.models import Status
from .misc import (
    get_api, read_json,
    write_json,
    SESSION_FILE
)


TWEETS = "tweets"
IDLIST = "index_list"


class NiceBaseClass(object):
    def __init__(self):
        pass

    @classmethod
    def from_dict(cls, d):
        _obj = cls()
        for key, value in d.items():
            _obj.__getattribute__(key).from_dict(value)
        return _obj

    @classmethod
    def from_session_file(cls, fname):
        d = read_json(fname)
        return cls.from_dict(d)


class Preppy(NiceBaseClass):
    def __init__(self):
        """
        Return an instance of Preppy class
        """
        super(NiceBaseClass, self).__init__()
        self.tweets = TweetList()
        self.index_table = IdTable()
        self.api = get_api()

    @property
    def as_dict(self):
        """
        Method for returning the contents of this object as a dictionary
        :return:
        """
        output = dict()
        output["tweets"] = self.tweets.as_dict
        output["index_table"] = self.index_table.as_dict
        return output

    @property
    def terms(self):
        return self.index_table.terms

    def add_search_term(self, term):
        """
        Set a new search term
        :param str term: Search term defining one search
        :return: NoneType
        """
        self.index_table.add_term(term)

    def load_stored_tweets(self, session_file_name):
        """
        Load a session file at any time
        :return: NoneType. Adds tweets to tweet
            list (that aren't already present)
        """
        tweet_dict = read_json(session_file_name)
        self.tweets.add_tweets(tweet_dict["tweets"])

    def run(self):
        """
        #--------------------------------------------------------- a landmark -
        # - Run preppy session ------------------------------------------------
        #----------------------------------------------------------------------
        :return: NoneType
        """
        for term in self.terms:
            self.sequentially_search(term)
        self.write_session_file()

    def sequentially_search(self, term, lang='en'):
        """
        Sequentially search for term $term
            The max_iter=180 implies the maximum number
            of tweets that can be collected per run (~18000)
        :param str term: search term
        :param str lang: Tweet language.
        :return: NoneType. Modifies self.tweets in place
        """
        i = 0
        max_iter = 180
        query = {"term": [term],
                 "count": 100,
                 "lang": lang,
                 "result_type": "recent"}
        tweet_dict = dict()  # Temporary container for tweets
        id_set = set()
        while i < max_iter:
            n1 = len(tweet_dict)
            i += 1
            min_id = min(id_set) if id_set else None
            if min_id:
                query.update({"max_id": str(min_id)})
            tweet_list = self.api.GetSearch(**query)
            tweet_dict.update({tweet.id_str: tweet
                               for tweet
                               in tweet_list})
            id_set.update([tweet.id for tweet in tweet_list])
            n2 = len(tweet_dict)
            n = n2 - n1
            if n == 0:
                break
        self.add_tweets(tweet_dict, term)

    def add_tweets(self, tweetlist, term):
        len1 = len(self.tweets)
        id_list = self.tweets.add_tweets(tweetlist)
        self.index_table.make_connections(term, id_list)
        len2 = len(self.tweets)
        return len2 - len1

    def write_session_file(self):
        """
        Write a json file of the current session
        :return: NoneType
        """
        output = self.as_dict
        write_json(output, SESSION_FILE)


class TweetList(NiceBaseClass):
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
        super(NiceBaseClass, self).__init__()
        if tweets is None:
            self.tweets = {}
        else:
            self.tweets = {id_str: Status(**tweet)
                           for id_str, tweet
                           in tweets.items()}

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
        return len(self.geotagged)

    @property
    def geotagged(self):
        geo_tweets = {id_str: tweet
                      for id_str, tweet
                      in self.tweets.items()
                      if "place" in tweet.AsDict()}
        return geo_tweets

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
        print("Added {:d} tweets".format(n_added))
        return id_list


class IdTable(NiceBaseClass):
    def __init__(self, d=None):
        super(NiceBaseClass, self).__init__()
        if type(d) is dict:
            self._idtable = {search_term: set(id_set)
                             for search_term, id_set
                             in d.items()}
        else:
            self._idtable = {}

    def add_term(self, term):
        if term in self._idtable:
            return
        self._idtable[term] = set({})

    @property
    def as_dict(self):
        output = {search_term: list(id_set)
                  for search_term, id_set
                  in self._idtable.items()}
        return output

    @classmethod
    def from_dict(cls):

    @property
    def terms(self):
        return sorted(list(self._idtable.keys()))

    def make_connection(self, term, id_str):
        """
        Connect a search term to a tweet ID
        :param term: The search term
        :param id_str: The Tweet ID string
        :return: NoneType
        """
        if term not in self._idtable:
            self.add_term(term)
        self._idtable[term].add(id_str)

    def make_connections(self, term, id_str_list):
        """
        Add multiple tweet id strings to a
        specified search term in the table
        :param term: The search term
        :param id_str_list: List of Tweet ID strings
        :return: NoneType
        """
        if term not in self._idtable:
            self.add_term(term)
        self._idtable[term].update(id_str_list)


if __name__ == "__main__":
    Session = Preppy()
    Session.add_search_term("Truvada")
    Session.run()
    print("There are {:d} tweets stored".format(Session.tweets.n))
    print("Of those, {:d} are geo-tagged".format(Session.tweets.n_geotagged))
