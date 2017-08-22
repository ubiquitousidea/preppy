from numpy.random.mtrand import choice
from pandas import DataFrame
from preppy import (
    TweetList, Preppy
)
from preppy.tweet_properties import (
    get_country, get_date, get_id, get_latitude,
    get_longitude, get_place, get_region,
    get_state, get_text, get_user_id
)


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
        table = self.table
        counts = table.country.value_counts()
        if min_count > 0:
            counts = counts[counts >= min_count]
        return counts

    def state_counts(self, min_count=3):
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
        :param tweets: list of Tweets (twitter.Status instances)
        :return: pandas.DataFrame
        """
        if tweets is None:
            tweets = list(self.tweets.tweets.values())
            tweets.sort(key=lambda tweet: tweet.id)


        column_getters = (
            ("id", get_id),
            ("date", get_date),
            ("user", get_user_id),
            ("text", get_text),
            ("place", get_place),
            ("country", get_country),
            ("longitude", get_longitude),
            ("latitude", get_latitude),
            ("state", get_state),
            ("us_region", get_region)
        )
        column_order = [column_getter[0]
                        for column_getter
                        in column_getters]
        output_dict = {
            key: [
                fn(tweet)
                for tweet
                in tweets
            ]
            for key, fn
            in column_getters
        }
        output = DataFrame.from_dict(output_dict)
        output = output[column_order]
        return output

    def write_report_geo(self, path):
        report = self.table_geo
        report.to_csv(path)

    def get_random_tweet(self):
        id_str = choice(self.tweets.id_list)
        return self.tweets[id_str]

    def get_random_geo_tweet(self):
        id_str = choice(self.tweets.id_list_geo)
        return self.tweets[id_str]