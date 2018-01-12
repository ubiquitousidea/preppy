# Build a classifier
# Save it to JSON
# Load the params from JSON


from numpy.random import choice
from preppy.binaryclassifier import TweetClassifier
from preppy.tweet_list import TweetList
from preppy.crossvalidator import CrossValidator
from preppy.preptweet import PrepTweet


tweet_list = TweetList.from_session_file()
some_tweets = tweet_list.as_list(coded_for="RELEVANCE", randomize=True)
print(some_tweets.__len__())
tc = TweetClassifier(variable_name="RELEVANCE")
tc.train(tweets=some_tweets)
for tweet in choice(some_tweets, 20):
    predicted_relevance = tc.predict(tweet)
    actual_relevance = tweet.lookup("relevance")
    print("Relevance: {}, Predicted Relevance: {}; text: {}"
          .format(actual_relevance, predicted_relevance, tweet.text))

cv = CrossValidator(tc)
rate = cv.misclass_rate(some_tweets)
print("Cross Validation Misclassification Rate: {}".format(rate))