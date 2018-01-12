"""
A cross validator class
"""

from sklearn.model_selection import KFold
from numpy import array
from preppy.binaryclassifier import TweetClassifier


class CrossValidator(object):
    def __init__(self, model):
        assert isinstance(model, TweetClassifier)
        self.model = model
        self.tweets = None
        self.variable_name = model.variable_name

    def misclass_rate(self, tweets, kfolds=3):
        """
        Return the error metric in cross validation (mis-classification rate)
        rate = (false negatives + false positives) / total predictions
        :param tweets: list of tweets
        :param kfolds: Number of groups to withhold and refit.
        :return:
        """
        tweets = array(tweets)
        result = []
        n_total = len(tweets)
        kf = KFold(n_splits=kfolds).split(tweets)
        for i_train, i_test in kf:
            train = tweets[i_train]
            test  = tweets[i_test]
            model = TweetClassifier(self.variable_name)
            model.train(tweets=train)
            # The predictors found in the training set will
            # be different for each fold.
            predicted = model.predict(tweets=test.tolist())
            actual = [tweet.lookup(self.variable_name)
                      for tweet in test]
            actual = array(actual)
            n = len(test)
            rate = sum(predicted != actual) / n
            result.append((n, rate))
        average_misclass_rate = \
            sum([n * rate / n_total for n, rate in result])
        return average_misclass_rate
