"""
This will be a class that implements a model of a binary outcome which will be known in
a series of cases. Concretely, we want to model the relevance of a tweet object given
the series of tweets and their manually coded relevance scores.

Where are the tweets stored? A TweetList. Each element of the TweetList is a PrepTweet object.
Code the relevance of the tweets manually (grad students) and store this in their metadata
attributes which are MetaData objects.

Pass the model a series of these Tweets with relevance coded. Iteratively update a model that
looks for the most discriminating feature of each tweet. Features can be presence of words, lack
of words (the logical inverse). The model F(tweet) takes the form of series of boolean algebra operations.
To construct discriminating statements, we will use boolean addition (OR) and boolean multiplication (AND)

F(tweet) = f1(tweet) + f2(tweet)
f1(tweet) :: does the tweet contain the hashtag #LGBT?
f2(tweet) :: does the tweet contain the hashtag #bbbh?
F(tweet)  :: does the tweet contain #LGBT or contain #bbbh?

Consider, however, that lacking a irrelevance indicator doesn't mean the tweet is relevant.
Lacking this indicator merely doesn't disqualify the tweet.

How about:
A model of relevance and irrelevance. We should have a model that says the tweet must be both
relevant and not irrelevant. Achieve this with negation and boolean multiplication.

R(tweet)  :: does the tweet contain any indicators of relevance
I(tweet)  :: does the tweet contain any indicators of irrelevance
~I(tweet) :: does the tweet contain no indicators of irrelevance
F(tweet)  == R(tweet) * ~I(tweet)
F(tweet)  :: relevant and not irrelevant

The form of this model is two boolean sums, one negated, and them multiplied.
The trouble will be finding the most discriminating indicators to start with.
This model probably will depend on use of a good prior. Take the first N training
observations. Take the set difference of their words (maybe hashtags too) in
both directions

Wr  :: the set of words used in all the relevant tweets
Wi  :: the set of words used in all the irrelevant tweets
Wip == Wi - Wr  (P is for possible)
Wip :: the set of words that appear in Irrelevant tweets but none of those that appear in Relevant tweets
Wrp == Wr - Wi
Wrp :: the set of words that appear in Relevant tweets but none of those that appear in Irrelevant tweets

Of the possible words, see which discriminate in cross validation the best.
That is, divide the training set into 80% -> Train, 20% -> Test
Train a model to discriminate on a subset of the words (as described above)
Predict the relevance F(tweet) of the test set and measure the error rate.
Iterate to find the set of words that minimizes cross validation error metric.

"""