from numpy.random.mtrand import choice, shuffle
from pandas import DataFrame
from preppy import (
    TweetList, Preppy
)
from preppy.preptweet import PrepTweet
from preppy.misc import write_json, enforce_extension, get_logger


logger = get_logger(__file__)


class ReportWriter(object):
    def __init__(self, tweets):
        """
        Instantiate a ReportWriter using a TweetList
        :param tweets:
        """
        if isinstance(tweets, TweetList):
            tweets = tweets
        elif isinstance(tweets, Preppy):
            tweets = tweets.tweets
        else:
            raise TypeError(
                "Argument must be either a Preppy "
                "session or a TweetList"
            )
        self.tweets = tweets
        self.table = self.make_table()

    def how_many_geotagged(self):
        return self.tweets.n_geotagged

    @property
    def geotagged(self):
        """
        A list the geotagged tweets.
        :return: list of PrepTweet objects
        """
        return self.tweets.as_list(only_geo=True)

    @property
    def table_all(self):
        return self.make_table()

    @property
    def table_geo(self):
        tweets = self.tweets.as_list(only_geo=True)
        return self.make_table(tweets)

    @property
    def table_nlu(self):
        tweets=self.tweets.as_list(coded_for="nlu")
        return self.make_table(tweets)

    def country_counts(self, min_count=5):
        table = self.table
        counts = table.country.value_counts()
        if min_count > 0:
            counts = counts[counts >= min_count]
        return counts

    def state_counts(self, min_count=5):
        table = self.table
        counts = table.state.value_counts()
        if min_count > 0:
            counts = counts[counts >= min_count]
        return counts

    def unique_states(self):
        table = self.table
        state_set = set(table.state)
        state_set.difference_update([None])
        states = sorted(list(state_set))
        return states

    def make_table(self, tweets=None):
        """
        Return a pandas.DataFrame table of tweet information

        Developer notes:
        To add a column to this report, write a property in PrepTweet class that
        can extract the information you want from itself.

        Then add a tuple to the column_getters tuple:
        tuple[0] should contain the column name
        tuple[1] should contain the name of the property that will
            be called (using getattr)

        :param tweets: list of Tweets (twitter.Status instances)
        :return: pandas.DataFrame
        """
        if tweets is None:
            tweets = self.tweets.as_list()

        # Add column names and information getter functions here.
        column_getters = (
            ("id_string", "id_str"),
            ("date", "date"),
            ("user", "user_id_str"),
            ("place", "place"),
            ("user_place", "user_place"),
            ("country", "country"),
            ("longitude", "longitude"),
            ("latitude", "latitude"),
            ("state", "state"),
            ("us_region", "region"),
            ("text", "text"),
            ("hashtags", "hashtags"),
            ("relevance", "is_relevant"),
            ("truvada_sentiment_score", "sentiment")
        )

        column_order = [column_getter[0]
                        for column_getter
                        in column_getters]
        output_dict = {
            col_name: [
                getattr(tweet, tweet_property_name)
                for tweet in tweets
            ]
            for col_name, tweet_property_name
            in column_getters
        }
        output = DataFrame.from_dict(output_dict)
        output = output[column_order]
        return output

    def hashtag_table(self, output_file_name=None, min_freq=None):
        """
        Create a dict of all hashtags counting up how many
        relevant tweets and how many irrelevant tweets used
        that tag.
        :param output_file_name: optional output file name
            (will be json)
        :param min_freq: Minimum number of hashtag observations
            to be included in the table
        :return: dict of the form:
            {hashtag: {RELEVANT: int, IRRELEVANT: int},...}
            write JSON file if output_file_name is provided
        """
        # Dict keys
        RELEVANT = "RELEVANT"
        IRRELEVANT = "IRRELEVANT"
        UNKNOWN = "UNKNOWN"
        SPECIFICITY = "SPECIFICITY"
        hashtag_table = {}

        for tweet in self.tweets.as_list():
            assert isinstance(tweet, PrepTweet)
            relevant = tweet.relevance
            hashtags = tweet.hashtags
            if not hashtags:
                continue
            for tag in hashtags:
                if tag not in hashtag_table:
                    hashtag_table[tag] = {
                        RELEVANT: 0,
                        IRRELEVANT: 0,
                        UNKNOWN: 0
                    }
                if relevant == 1:
                    hashtag_table[tag][RELEVANT] += 1
                elif relevant == 0:
                    hashtag_table[tag][IRRELEVANT] += 1
                else:
                    hashtag_table[tag][UNKNOWN] += 1

        if min_freq is not None:
            min_freq = max(0, int(min_freq))
            output = {tag: usage for tag, usage
                      in hashtag_table.items()
                      if sum(usage.values()) >= min_freq}
        else:
            output = hashtag_table

        for usage in output.values():
            # difference between usage count in
            # relevant and irrelevant tweets
            # divided by total number of usages
            total = usage[RELEVANT] + usage[IRRELEVANT]
            diff = usage[RELEVANT] - usage[IRRELEVANT]
            usage.update({
                SPECIFICITY: diff / total if total > 0 else 0.0
            })

        if output_file_name:
            enforce_extension(output_file_name, ".json")
            write_json(output, output_file_name)
        return output

    def select_factors(self):
        """
        Use the relevance data in conjunction with hashtag presence
        to decide which hashtags might be best predictors for
        a model that predicts relevance

        Pseudo-code:

        . Obtain set of words present in relevant tweets
        . Obtain set of words present in irrelevant tweets
        . First, try set diff, both ways, to find words
            that are most specific indicators of relevance
            and irrelevance.

        :return: list of strings
        """
        relevant_words = {}  # a set
        for tweet in self.tweets.relevant:
            assert isinstance(tweet, PrepTweet)
            relevant_words.update(tweet.text.split())

        irrelevant_words = {}  # a set
        for tweet in self.tweets.irrelevant:
            assert isinstance(tweet, PrepTweet)
            irrelevant_words.update(tweet.text.split())
        return None

    def write_report_nlu(self, path, fmt='csv'):
        """
        TODO write a make_report(self,var) method, this is not DRY at all.
        :param path:
        :param fmt:
        :return:
        """

        report = self.table_nlu
        if fmt == 'csv':
            report.to_csv(path)
        elif fmt == "excel" or fmt == "xls":
            report.to_excel(path)
        else:
            raise IOError("{:} is not a valid "
                          "output format for this "
                          "report.".format(fmt))

    def write_report_geo(self, path, fmt='csv'):
        """
        Write a tabular report containing the tweets and their metadata
        only including geotagged tweets (geotaggedness determined from
        the tweet.place attribute being not None). tweet.place will be
        a dict if the tweet is geotagged.
        :param path:
        :param fmt:
        :return:
        """
        report = self.table_geo
        if fmt == 'csv':
            report.to_csv(path)
        elif fmt == "excel" or fmt == "xls":
            report.to_excel(path)
        else:
            raise IOError("{:} is not a valid "
                          "output format for this "
                          "report.".format(fmt))

    def write_report_coded(self, path, fmt=None):
        """
        Write a report of the tweets that have been coded for
        relevance (both relevant and irrelevant ones)
        :param path: file path of the csv file to be written
        :return: NoneType
        """
        if fmt is None:
            fmt = 'csv'
        tweets = self.tweets.relevant + self.tweets.irrelevant
        shuffle(tweets)
        report = self.make_table(tweets)
        if fmt == "csv":
            report.to_csv(path)
        elif fmt == "excel" or fmt == "xls":
            report.to_excel(path)
        else:
            raise IOError("{:} is not a valid "
                          "output format for this "
                          "report.".format(fmt))

    def write_report_all(self, path, fmt=None):
        if fmt is None:
            fmt = 'csv'
        report = self.make_table()
        if fmt == 'csv':
            report.to_csv(path)
        elif fmt == "excel" or fmt == "xls":
            report.to_excel(path)
        else:
            raise IOError("{:} is not a valid "
                          "output format for this "
                          "report.".format(fmt))

    def get_random_tweet(self):
        id_str = choice(self.tweets.id_list)
        return self.tweets[id_str]

    def get_random_geo_tweet(self):
        id_str = choice(self.tweets.id_list_geo)
        return self.tweets[id_str]