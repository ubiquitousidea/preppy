"""
Initially, a twitter listener to determine the magnitude and location of public
discussion of PrEP (Truvada) on Twitter.

Future work may include expansion to other social media API"s and other health
topics. This will ultimately be the backend code used on a web based graphical
user interface to ask questions relevant to HIV researchers. Python chosen as
the language because of the Tornado and Scikit-Learn packages.
"""

from getpass import getuser
from preppy.dataobjects import PlaceInfo
from preppy.misc import (
    get_twitter_api, write_json,
    backup_session, make_list, cull_old_files,
    ask_param, MISSING, rehydrate_tweets,
    get_logger, read_rscript_output
)
from preppy.metadata import CODE_BOOK, place_of_interest
from preppy.preptweet import PrepTweet
from preppy.tweet_list import TweetList


logger = get_logger(__file__)


class Preppy(object):
    def __init__(self, session_file_path,
                 backup_dir=None,
                 config_file=None,
                 place_info="place_info.json"):
        """
        Return an instance of Preppy class
        :param str session_file_path: Name of a session file (optional)
        :param backup_dir: path to backups directory
        :param config_file: path to configuration file that contains the API keys
        :param place_info: path to the place info file (from PlaceInfo.to_json())
        """
        self.session_file_path = session_file_path
        if session_file_path:
            self.tweets = TweetList.from_session_file(
                self.session_file_path)
        else:
            self.tweets = TweetList()
        self.backups_dir = backup_dir
        self.api = get_twitter_api(config_file)
        self.placeinfo = PlaceInfo.from_json(fname=place_info, config_file=config_file)

    @property
    def as_dict(self):
        """
        Method for returning the contents of this object as a dictionary
        :return:
        """
        output = self.tweets.as_dict
        return output

    def status_prior(self, _term=None):
        """
        State how many tweets there are
        Optionally include a message about which term is going to be searched
        :param _term: Optional. Term being searched
        :return: NoneType
        """
        logger.info("There are {:d} tweets.".format(self.tweets.n))
        if _term is not None:
            logger.info("Retrieving more tweets related to {:}".format(_term))


    def status_posterior(self):
        logger.info("There are {:d} tweets now".format(self.tweets.n))
        logger.info("Of those, {:d} are geo-tagged".format(self.tweets.n_geotagged))

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

    def sequentially_search(self, terms, lang='en',
                            last_session_backstop=False):
        """
        Sequentially search for term $term
        :param {tuple, list} terms: list of search terms
        :param str lang: Tweet language.
        :param BoolType last_session_backstop: If true, search
            only covers that which wasn't covered in previous run.
            Use False if starting a new keyword when previous
            session did not use that keyword.
        :return: NoneType. Modifies self.tweets in place
        """
        terms = make_list(terms)
        min_id = self.tweets.max_id \
            if last_session_backstop else None
        for term in terms:
            query = {
                "term": term,
                "count": 100,
                "lang": lang,
                "result_type": "recent"
            }
            if min_id is not None:
                query.update({"since_id": min_id})
            tweet_list = self.search_single_term(query)
            n_added = self.add_tweets(tweet_list)
            logger.info("Added {:d} tweets related to {:}"
                        .format(n_added, term))

    def search_single_term(self, query):
        """
        Search using a query dictionary

        This method actually contains the
            twitter.Api.GetSearch call

        :param query: dictionary of search arguments
        :return: TweetList object
        """
        i = 0
        max_iter = 180
        tweet_list = TweetList()  # an empty TweetList
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
        return tweet_list

    def add_tweets(self, tweets):
        """
        Add tweets from a list or dict
        :param tweets: list, dict, or TweetList; see TweetList.add_tweets
        :return: integer; Change in size of the tweet list
        """
        len1 = len(self.tweets)
        self.tweets.add_tweets(tweets)
        len2 = len(self.tweets)
        return len2 - len1

    def encode_user_location(self, nmax=None):
        """
        For each tweet that has user location attribute, encode location
        coordinates for that tweet using the PlaceInfo class (which uses
        the Google Geocoding API)
        :return: NoneType
        """
        n = 0
        for tweet in self.tweets.tweets.values():
            assert isinstance(tweet, PrepTweet)
            place_name = tweet.user_place
            if place_name is None or not place_of_interest(place_name):
                continue
            coords = self.placeinfo.get_coordinates(place_name)
            if coords:
                logger.info("Place Name: {}, Coordinates {}".format(place_name, coords))
                tweet.metadata.record(
                    param="user_place_coordinates",
                    user_id="google_geocoding",
                    value=coords
                )
                n += 1
            if n >= nmax:
                break
        logger.info("Successfully encoded {} user place coordinates".format(n))
        logger.info("Did so by making {} api calls to Google".format(self.placeinfo.api_counter))
        self.placeinfo.to_json("place_info.json")

    def encode_rscript_results(self):
        relevant_ids = read_rscript_output("relevant_ids.csv")
        for ID, tweet in self.tweets.tweets.items():
            assert isinstance(tweet, PrepTweet)
            if ID in relevant_ids:
                tweet.metadata.record(
                    param="relevance",
                    user_id="keyword_classify.R",
                    value=1
                )
            else:
                tweet.metadata.record(
                    param="relevance",
                    user_id="keyword_classify.R",
                    value=0
                )
        # TODO add logging information



    def rehydrate_tweets(self):
        """
        Rehydrate tweets from web
        """
        id_list = self.tweets.id_list
        tweets_dict = rehydrate_tweets(id_list, self.api)
        tweets_added = len(tweets_dict)
        logger.info("Rehydrated {:} tweets".format(tweets_added))
        self.add_tweets(tweets_dict)

    def encode_variable(self,
                        variable_name,
                        user_id=None,
                        only_geo=True,
                        max_tweets=100,
                        randomize=True):
        """
        User interaction.
        Ask user to encode a variable
        Record the value as an item of metadata
            in self._metadata
        :param variable_name: the name of the variable to encode
            (must be in CodeBook)
        :param {int, str} user_id: The identifier assigned
            to a user when performing this variable encoding
        :param BoolType only_geo: if True, only iterate
            through the tweets which are geotagged
        :param int max_tweets: How may tweets to encode before retiring
        :param randomize: If true, randomly select tweet order
        :return: NoneType. Modifies self._metadata in place.
        """
        variable_name = variable_name.upper()
        assert CODE_BOOK.has_variable(variable_name)
        user_id = getuser() if user_id is None else user_id
        possible_values = CODE_BOOK.possible_values(variable_name)
        tweets = self.tweets.as_list(only_geo, randomize)
        tweet_count = 0
        for tweet in tweets:
            assert isinstance(tweet, PrepTweet)
            if self.tweets.user_has_encoded(
                    user_id, variable_name, tweet.id_str):
                # If this user has already encoded that
                # variable, do not show the tweet again
                continue

            p_relevance = tweet.relevance

            if variable_name != "RELEVANCE" \
                    and p_relevance is not None \
                    and p_relevance < 0.5:
                # If encoding another variable other than
                # relevance, only show the tweet it is relevant
                continue

            param_val = MISSING
            max_iter = 10
            i = 0
            while i < max_iter:
                i += 1
                param_val = ask_param(
                    param_name=variable_name,
                    tweet=tweet,
                    api=self.api
                )
                if param_val in possible_values:
                    break
                else:
                    msg = "Possible values: {:}"
                    value = CODE_BOOK.explain_possible_values(variable_name)
                    logger.info(msg.format(value))
            self.tweets.record_metadata(
                id_str=tweet.id_str,
                param=variable_name,
                user_id=user_id,
                value=param_val
            )
            tweet_count += 1
            if max_tweets != 0 and tweet_count >= max_tweets:
                break

    def write_session_file(self):
        """
        Write a json file of the current session
        :return: NoneType
        """
        output = self.as_dict
        write_json(output, self.session_file_path)

    def cleanup_session(self):
        self.write_session_file()
        backup_session(self.backups_dir, self.session_file_path)
        cull_old_files(self.backups_dir, n_keep=10)
