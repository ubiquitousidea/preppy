from preppy.preptweet import PrepTweet
from preppy.metadata import MetaData
from sklearn.ensemble import RandomForestClassifier

from numpy import (
    zeros_like, vectorize
)


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

    def train(self, *tweets, variable_name=None):
        """
        Using words in self.indicator_words, train the model using indicator variables
        as predictors.

        :param tweets: arbitrary number of PrepTweet objects
        :param variable_name: name of the variable to train on (may already be set by __init__)
        :return: NoneType
        """
        if variable_name is not None:
            self.variable_name = variable_name

        response = []
        for tweet in tweets:
            assert isinstance(tweet, PrepTweet)
            value = tweet.lookup(self.variable_name)
            words = tweet.words
            response.append(value)

        self.factor_select_initial()  # self.indicator_words is set by this function

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
        prediction = self.model.predict(indicators)
        return prediction

    def evaluate_indicators(self, tweet_words):
        """
        Vectorize the operation of evaluating presence of each
        :param tweet_words: set of words observed
        :return: list of integers
        """
        tweet_words = set(tweet_words)
        evaluate = vectorize(lambda _word: int(_word in tweet_words))
        indicators = evaluate(self.indicator_words)
        return indicators

    @staticmethod
    def assert_all_elements_are_strings(words):
        assert all([type(item) is str for item in words])

    def factor_select_initial(self):
        """
        A preliminary factor selection step to reduce the number of
        choices given to the predictive model
        :return: NoneType
        """

        pass

    def add_words(self, words, value):
        """
        Having observed words associated with value = (True/False)
        :param words: list of character strings
        :param value: True/False
        :return: NoneType
        """
        value = str(value)  # make safe for json I/O
        assert self.assert_all_elements_are_strings(words)
        if value not in self.words:
            self.words[value] = set({})
        wordset = self.words.get(value)
        wordset.update(words)



