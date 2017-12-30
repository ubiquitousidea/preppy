"""A module for text analytics through IBM Watson

Currently a standalone utility, to be worked into preppy. 

Inputs: a preppy json file of tweets coded as relevant.
Outputs: same json file, with additional subdict within a tweet called 'nlu' containing
    Watsons NLU output for the tweet. 
"""

import watson_developer_cloud
import watson_developer_cloud.natural_language_understanding.features.v1 as features
from creds import creds
import json

with open("relevant_tweets.json") as f:
    tweets = json.load(f)

nlu = watson_developer_cloud.NaturalLanguageUnderstandingV1(
    username=creds['username'],
    password=creds['password'],
    version="2017-02-27")

def nlp(txt):
    result = nlu.analyze(text=txt,
        features = [features.Concepts(), features.Keywords(), features.Emotion(), features.Sentiment()])
    return result

for k in tweets.keys():
    try:
        tweet_text = tweets[k]['full_text']
        print("Analyzing tweet %s" % k)
        tweets[k]['nlu'] = nlp(tweet_text)
    except watson_developer_cloud.watson_developer_cloud_service.WatsonException:
        print("WatsonExcepption on %s" % k)
        tweets[k]['nlu'] = None
        pass
    except KeyError: 
        print("KeyError on tweet %s" % k)
        tweets[k]['nlu'] = None
        pass


with open("test_watson.json", "w") as f:
    f = json.dumps(tweets, f, indent=4)