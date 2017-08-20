import os

from numpy import array, zeros
from numpy.random.mtrand import choice
from pandas import DataFrame
from twitter import Status

from preppy import (
    TweetList, Preppy,
    MISSING, read_json
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

        missing = MISSING
        valid_state_codes = read_json(
            "{:}/state_codes.json".format(os.path.dirname(__file__)))\
            ["valid_state_codes"]

        def get_id(tweet):
            return tweet.id

        def get_date(tweet):
            return tweet.created_at

        def get_user_id(tweet):
            try:
                return tweet.user.id
            except:
                return missing

        def get_text(tweet):
            try:
                if tweet.full_text:
                    return tweet.full_text
                elif tweet.text:
                    return tweet.text
                else:
                    return missing
            except:
                return missing

        def get_place(tweet):
            try:
                return tweet.place["full_name"]
            except:
                return missing

        def get_centroid(tweet):
            try:
                bounding_box = array(
                    tweet.place
                    ["bounding_box"]
                    ["coordinates"]
                    ).squeeze()
                centroid = bounding_box.mean(axis=0)
                return centroid
            except:
                return zeros(2)

        def get_longitude(tweet):
            try:
                centroid = get_centroid(tweet)
                return centroid[0]
            except:
                return missing

        def get_latitude(tweet):
            try:
                centroid = get_centroid(tweet)
                return centroid[1]
            except:
                return missing

        def get_country(tweet):
            assert isinstance(tweet, Status)
            try:
                return tweet.place["country"]
            except:
                return missing

        def get_state(tweet):
            """
            Get the state in which the tweet originated
            Currently relies upon the JSON response from twitter API
            Consider future use of Google reverse geocoding API

            Information page:
            https://developers.google.com/maps/documentation/geocoding/start

            Example:
            https://maps.googleapis.com/maps/api/geocode/json?latlng=40.714224,-73.961452&key=...

            :param tweet:
            :return:
            """
            assert isinstance(tweet, Status)
            state_code = missing
            try:
                country_code = tweet.place["country_code"]
            except TypeError:
                return missing
            place_type = tweet.place["place_type"]
            if country_code == "US" and place_type == "city":
                full_name = tweet.place["full_name"]
                state_code = full_name.split(",")[-1].strip().upper()
                state_code = state_code if state_code in valid_state_codes else missing
            else:
                pass
            return state_code

        def get_region(tweet):
            """
            Get the region of the US a tweet originated from
            :param tweet:
            :return:
            """
            return missing

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