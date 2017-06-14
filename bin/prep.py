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


class Preppy(object):
    """
    Class object for session of Preppy, the friendly HIV web crawler.
    Preppy takes your questions and obtains through various means
    the prevalence of certain search terms in the twitter sphere
    using both the twitter search api and twitter streaming api.
    Preppy can answer questions like:
        Preppy, would you please tell me which city has more people
        talking about side effect xyz associated with drug abc?

        Other useful stuff here...
    """

    def __init__(self):
        """
        Return an instance of Preppy class
        """
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
        Run preppy session
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
        while i < max_iter:
            i += 1
            min_id = self.tweets.min_id
            if min_id and i != 1:
                query.update({"max_id": min_id})
            result = self.execute_query(query)
            n = self.add_tweets(result, term)
            if n == 0:
                break

    def add_tweets(self, tweetlist, term):
        len1 = len(self.tweets)
        id_list = self.tweets.add_tweets(tweetlist)
        self.index_table.make_connections(term, id_list)
        len2 = len(self.tweets)
        return len2 - len1

    def execute_query(self, q):
        """
        Wrapper for twitter.api.GetSearch
        :param q: query dictionary
        :return: list of tweets
        """
        return self.api.GetSearch(**q)

    def write_session_file(self, append=True):
        """
        Write a json file of the current session
        :param BoolType append: If True, Preppy
            will open last session file and
            append to it. Tweets collected
            in this session take precedence
            over ones in the existing file
        :return: NoneType
        """
        output = self.as_dict

        write_json(output, SESSION_FILE)


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
        self.keyword_table = {}

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
        :return: NoneType
        """
        id_str = tweet.id_str
        self.tweets.update({id_str: tweet})

    def add_tweets(self, tweetlist):
        """
        Add a list of tweets to the tweet list
        :param tweetlist: list of <twitter.Status> instances
        :return: List of ID strings that were added
        """
        len_1 = len(self.tweets)
        id_list = []
        for tweet in tweetlist:
            id_list.append(tweet.id_str)
            self.add_tweet(tweet)
        len_2 = len(self.tweets)
        dl = len_2 - len_1
        print("Added {:d} tweets".format(dl))
        return id_list


class IdTable(object):
    def __init__(self, d=None):
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

    def ask_a_question(self, question):
        """
        Answer the question you have
        :param question: a question
        :return: the answer
        """
        # TODO: answer a question here
        return question

if __name__ == "__main__":
    Session = Preppy()
    Session.add_search_term("Truvada")
    Session.run()
    print("There are {:d} tweets stored".format(Session.tweets.n))
    print("Of those, {:d} are geo-tagged".format(Session.tweets.n_geotagged))
