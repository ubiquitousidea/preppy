"""
Initially, a twitter listener to determine the magnitude and location of public
discussion of PrEP (Truvada) on Twitter.

Future work may include expansion to other social media API"s and other health
topics. This will ultimately be the backend code used on a web based graphical
user interface to ask questions relevant to HIV researchers. Python chosen as
the language because of the Tornado and Scikit-Learn pacakges.
"""


from misc import get_api, write_json, write_tweet_list, anonymize
from twitter.models import Status
import json


class TweetList(object):
    """
    Class object for constructing a tweet container that
        automatically anonymizes, has methods for adding a
        tweet only if it is not present, and writing
        files.
    """

    def __init__(self, tweets=None):
        """
        Return an instance of the TweetList class
        :param tweets: dict
            {'tweet_id_01': <twitter.models.Status>,
             'tweet_id_02': <twitter.models.Status>,...}
        """
        self.tweets = {} if not tweets else tweets

    def __dict__(self):
        """
        Property to return json representation of this class
        The self.tweets dict is a dict of <twitter.models.Status> objects
        This method converts them to dictionaries (json)

        :return: dict of dict representations of tweets (Statuses)
        """
        return {k: v.AsDict() for k, v in self.tweets.items()}

    @classmethod
    def from_json(cls, fname):
        """
        Instantiate this this class from a JSON file
        :param fname: file name of the json file
        :return: Instance of this class
        """
        with open(fname, 'r') as fh:
            tweetlist = json.load(fh)["TWEETS"]
        return cls(tweetlist)

    def add_tweet(self, tweet):
        """
        Try adding a single tweet to the tweet list
        This uses the dict.update method which will
        overwrite any preexisting tweet of the same
        id (unique identifier string)
        :param tweet: Status or dict
        :return: NoneType
        """
        if isinstance(tweet, Status):
            tweet = tweet.AsDict()
        k = tweet["id_str"]
        tweet = anonymize(tweet)
        self.tweets.update({k: tweet})

    def add_tweets(self, tweetlist):
        """
        Add a list of tweets to the tweet list
        :param tweetlist: list of <twitter.models.Status> instances
        :return: integer, how many unique new tweets were added
        """
        len_1 = len(self.tweets)
        for tweet in tweetlist:
            self.add_tweet(tweet)
        len_2 = len(self.tweets)
        return len_2 - len_1

    def do_more_things(self, **kwargs):
        """
        Do arbitrarily useful things here.
        :param kwargs: Questions
        :return: Useful knowledge
        """


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

    def __init__(self, tweets=None):
        """
        Return an instance of Preppy class
        :param tweets: Optional list of
        """
        self.tweets = TweetList(tweets)  # Container for storing anonymized tweets
        self.term_list = []  # List of search terms, each one defining one 'search'
        self.search_history = []  # list of search dictionaries used

    def set_term(self, term):
        """
        Set a new search term
        :param term: Various formats:
            1:
            2:
            3:...
        :return: NoneType
        """
        self.term_list += [term]

    def run(self):
        """
        Run preppy session
        :return:
        """
        # Launch the historical search algorithm
        # Subprocess a streaming service that receives
        #   tweets of a given description as they are produced
        #
        # - Wrap this, and anticipate the rate limit:
        queries = self.generate_queries(100)
        self.execute_queries(queries)

        search1 = {"term": ["Truvada"],
                   "since": "2014-01-01",
                   "count": 100,
                   "lang": "en"}

        api = get_api()
        tweetlist = api.GetSearch(**search1)
        self.tweets.add_tweets(tweetlist)



if __name__ == "__main__":
    session = Preppy()
    session.set_term("Truvada")
    session.run()
