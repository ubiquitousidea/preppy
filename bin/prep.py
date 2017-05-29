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


class Point:
    def __init__(self, x, y):
        """
        Grid point for hex gridded search areas
        :param x: longitude of the search point
        :param y: latitude of the search point
        """
        self._x = 0.
        self._y = 0.
        self.x = x
        self.y = y

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, val):
        self._x = float(val)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, val):
        self._y = float(val)

    def translate(self, dx=None, dy=None):
        """
        Translate a point
        :param dx: change in longitude
        :param dy: change in latitude
        :return: NoneType. Modifies self in place
        """
        if dx:
            self.x += dx
        if dy:
            self.y += dy


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
           "count": 1}

tweetlist = t.GetSearch(**search1)


def write_json(_d, fn):
    """
    Write a dictionary to a file
    :param dict _d: dictionary of interest
    :param str fn: file name to be written
    :return: NoneType
    """
    with open(fn, "w") as fh:
        json.dump(_d, fh)


for tweet in tweetlist:
    d = tweet.AsDict()
    print(d)
    print(d.keys())
