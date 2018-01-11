from preppy.misc import get_logger, write_json, read_json, enforce_extension
from preppy.preptweet import PrepTweet
from preppy.metadata import MetaData
from sklearn.ensemble import RandomForestClassifier

from numpy import (
    zeros_like, vectorize, array
)


logger = get_logger(__file__)


class TweetClassifier(object):
    """
    An object to classify things
    """
    def __init__(self, variable_name):
        """
        (This may be slow since it's in interpreted Python. Check to see if there
        exists a python implementation for RandomForest model)

        Multinomial classifier

        Train this object with sets of indicators and an associated discrete variable.

        This object will make predictions about the value of this variable for
            observed sets of indicators

        :param variable_name: name of the variable that this model is concerned with
        """
        variable_name = str(variable_name).lower()
        assert variable_name in MetaData().variable_names()
        self.variable_name = variable_name

        # These are the words whose presence is used
        # as predictor matrix in classifier
        self.indicator_words = []

        # words dict:
        # primary key: value of the variable
        # secondary key: a set of words observed in
        # conjunction with that variable value.
        self.words = {}

        # use the RF model
        self.model = RandomForestClassifier()

    def train(self, tweets, variable_name=None):
        """
        Using words in self.indicator_words, train the model using indicator variables
        as predictors.

        :param tweets: list of PrepTweet objects
        :param variable_name: name of the variable to train on
            overrides what is set by __init__
        :return: NoneType
        """
        if variable_name is not None:
            self.warn_if_trained(self.variable_name, variable_name)
            self.variable_name = variable_name
        responses = []
        indicators = []
        for tweet in tweets:
            assert isinstance(tweet, PrepTweet)
            value = tweet.lookup(self.variable_name)
            words = tweet.words
            self.add_words(words=words, value=value)
            responses.append(value)
        self.factor_select_initial()
        for tweet in tweets:
            ind = self.evaluate_indicators(tweet.words)
            indicators.append(ind)
        x = array(indicators, ndmin=2, dtype=int)
        y = array(responses)
        self.model.fit(x, y)

    def predict(self, tweet):
        """
        Wrapper for the discriminant function
        :param tweet: PrepTweet object
        :return:
        """
        assert isinstance(tweet, PrepTweet)
        return self.discriminant(tweet.words)

    def discriminant(self, words):
        """
        Evaluate the discriminant function
        :param words: list or set of words observed
        :return: predicted value for the variable named in self.variable_name
        """
        indicators = self.evaluate_indicators(words)
        indicators = array(indicators, ndmin=2)  # I am fine with 1d arrays but scikit-learn raises deprecation warning
        prediction = self.model.predict(indicators)
        return prediction

    def evaluate_indicators(self, tweet_words):
        """
        Vectorize the operation of evaluating presence of each
        :param tweet_words: set of words observed
        :return: list of integers
        """
        if tweet_words is None:
            return [0. for word in self.indicator_words]
        tweet_words = set(tweet_words)
        evaluate = vectorize(lambda _word: int(_word in tweet_words))
        indicators = evaluate(self.indicator_words)
        return indicators

    def get_word_specificity(self):
        # TODO: Move this feature from the ReportWriter to this class
        pass

    def factor_select_initial(self):
        """
        A preliminary factor selection step to reduce the number of
        choices given to the predictive model
        Logic: use any 100% specific word as a potential indicator
        (words that appear only in a single factor level of the variable)
        :return: NoneType
        """
        indicators = set()
        factor_levels = self.words.keys()
        for level, words in self.words.items():
            other_levels = set(factor_levels) - {level}
            w1 = set(words)  # words associated with this factor level
            w2 = set()  # words associated with the other factor levels
            for other_level in other_levels:
                w2.update(self.words.get(other_level))
            specific_words = w1 - w2
            indicators.update(specific_words)
        self.indicator_words = list(indicators)

    def add_words(self, words, value):
        """
        Having observed words associated with value = $$$
        record the observed words
        :param words: list of character strings
        :param value: True/False
        :return: NoneType
        """
        if words is None:
            return
        value = str(value)  # make safe for json I/O
        self.assert_all_elements_are_strings(words)
        wordset = set(self.words[value]) if value in self.words else set()
        wordset.update(words)
        self.words[value] = wordset

    def warn_if_trained(self, v1, v2):
        if self.is_trained:
            if v1 != v2:
                msg = "Changing response from {} to {}".format(v1, v2)
                logger.warning(msg)

    @property
    def is_trained(self):
        """
        Say whether or not this model object has been trained
        :return: BoolType
        """
        return len(self.indicator_words) > 0

    def to_json(self, fname):
        """
        Write out the contents of this model to a json file
        :param fname: name of the json file to write
        :return:
        """
        fname = enforce_extension(fname, ".json")
        write_json(self.as_dict, fname)

    @classmethod
    def from_json(cls, fname):
        """
        Instantiate this class from a json file
        :param fname: name of the json file written by self.to_json()
        :return: an instance of this class
        """
        d = read_json(fname)
        return cls.from_dict(d)

    @property
    def as_dict(self):
        """
        Return a dictionary of this object
        Make the word sets into lists
        :return: dictionary
        """
        d = self.__dict__
        # convert to list to be json safe
        d['words'] = {value: list(words) for value, words in self.words.items()}
        d['model'] = dict(self.model.get_params())
        return d

    @classmethod
    def from_dict(cls, d):
        """
        Instantiate this class from a dict
        But make the word lists into sets
        :param d: dictionary produced by TweetClassifier().as_dict
        :return: an instance of this class
        """
        obj = cls()
        obj.__dict__.update(d)
        obj.words = {value: set(words) for value, words in d['words'].items()}

    @staticmethod
    def assert_all_elements_are_strings(words):
        assert all([type(item) is str for item in words])



