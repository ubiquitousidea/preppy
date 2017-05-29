"""
Initially, a twitter listener to determine the magnitude and location of public
discussion of PrEP (Truvada) on Twitter.

Future work may include expansion to other social media API"s and other health
topics. This will ultimately be the backend code used on a web based graphical
user interface to ask questions relevant to HIV researchers. Python chosen as
the language because of the Tornado and Scikit-Learn pacakges.
"""


import json
from twitter.api import Api


with open("./config.json", "r") as f:
    d = json.load(f)

A = d["A"]
B = d["B"]
C = d["C"]
D = d["D"]

t = Api(A, B, C, D)

search1 = {"term": ["Truvada"],
           "since": "2015-01-01",
           "until": "2017-05-29",
           "count": 100}

tweetlist = t.GetSearch(**search1)

for tweet in tweetlist:
    print(tweet.AsDict())
