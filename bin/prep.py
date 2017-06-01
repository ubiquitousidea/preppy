"""
Initially, a twitter listener to determine the magnitude and location of public
discussion of PrEP (Truvada) on Twitter.

Future work may include expansion to other social media API"s and other health
topics. This will ultimately be the backend code used on a web based graphical
user interface to ask questions relevant to HIV researchers. Python chosen as
the language because of the Tornado and Scikit-Learn pacakges.
"""


from misc import get_api, write_json, write_tweet_list


search1 = {"term": ["Truvada"],
           "since": "2014-01-01",
           "count": 100,
           "lang": "en"}

api = get_api()
tweetlist = api.GetSearch(**search1)
write_tweet_list(tweetlist, "tweets_03.json")
