"""
Initially, a twitter listener to determine the magnitude and location of public
discussion of PrEP (Truvada) on Twitter.

Future work may include expansion to other social media API"s and other health
topics. This will ultimately be the backend code used on a web based graphical
user interface to ask questions relevant to HIV researchers. Python chosen as
the language because of the Tornado and Scikit-Learn pacakges.
"""

import datetime
from misc import get_api, anonymize, \
    read_json, write_json, minidate
from twitter.models import Status


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
            {'tweet_id_01': {tweet dict},
             'tweet_id_02': {tweet dict},...}
        """
        self.tweets = {id_str: Status(**tweet) for id_str, tweet in tweets.items()} if tweets else {}

    def __dict__(self):
        """
        Property to return json representation of this class
        The self.tweets is a dict of <twitter.models.Status> objects
        This method converts the Status objects to dictionaries
        :return: dict of dict representations of tweets (Statuses)
        """
        return {k: v.AsDict() for k, v in self.tweets.items()}

    def __repr__(self):
        return self.__dict__()

    def add_tweet(self, tweet):
        """
        Try adding a single tweet to the tweet list
        This uses the dict.update method which will
        overwrite any preexisting tweet of the same
        id (unique identifier string)
        :param twitter.models.Status tweet: A tweet
        :return: NoneType
        """
        assert isinstance(tweet, Status)
        tweet = anonymize(tweet)
        self.tweets.update({
            tweet.id_str: tweet
        })

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
        pass


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

    def __init__(self, session_file=None):
        """
        Return an instance of Preppy class
        :param session_file: Optional file name of saved session
        """
        self.session_file = 'preppy_session.json' if session_file is None else str(session_file)
        session_dict = read_json(self.session_file)
        tweet_dict = {} if session_dict is None else session_dict["tweets"]
        self.tweets = TweetList(tweet_dict)
        self.term_list = []  # List of search terms, each one defining one 'search'
        self.api = get_api()

    def __dict__(self):
        output = {}
        output.update({
            "tweets": self.tweets.__dict__(),
            "term_list": self.term_list,
        })
        return output

    def set_term(self, term):
        """
        Set a new search term
        :param str term: Search term defining one search
        :return: NoneType
        """
        assert isinstance(term, str)
        self.term_list += [term]

    def run(self):
        """
        Run preppy session
        :return: NoneType
        """
        queries = self.generate_queries()
        self.execute_queries(queries)
        self.write_session_file()

    def write_session_file(self):
        """
        Write a json file of the current session
        :return: NoneType
        """
        output = self.__dict__()
        write_json(output, self.session_file)

    def generate_queries(self, lang="en"):
        """
        Generate search query dictionaries
        :param str lang: Language of interest
        :return: list of dictionaries
        """
        query_list = []
        for term in self.term_list:
            for since, until in self.get_dates():
                q = {"term": [term],
                     "since": since,
                     "until": until,
                     "count": 100,
                     "lang": lang}
                query_list.append(q)
        return query_list

    @staticmethod
    def get_dates():
        """
        Get a series of date ranges to search
        :return: list of 2-tuples of date strings
        """
        output = []
        n = 7  # Integer number of days
        time_span = datetime.timedelta(days=n)
        time_increment = datetime.timedelta(days=1)
        today = datetime.datetime.now()
        t1 = today - time_span
        for i in range(n):
            _t1 = t1 + (i + 0) * time_increment
            _t2 = t1 + (i + 1) * time_increment
            date_tuple = (minidate(_t1),
                          minidate(_t2))
            output.append(date_tuple)
        return output

    def execute_queries(self, query_list):
        """
        Call Twitter Search API repeatedly
        :param query_list: list of dictionaries
        :return: NoneType
        """
        for q in query_list:
            print(str(q))
            tweetlist = self.api.GetSearch(**q)
            n_added = self.tweets.add_tweets(tweetlist)
            print("{:d} tweets added".format(n_added))


if __name__ == "__main__":
    Session = Preppy('preppy_session.json')
    Session.set_term("Truvada")
    Session.run()
