"""
pseudocode

CustomStatus

"""

from twitter import Status


class PrepTweet(object):
    def __init__(self, d):
        self.status = Status()
        self.metadata = MetaData()
        self.watson_info = WatsonInf()

    def to_dict(self):
        return {}

    @classmethod
    def from_dict(cls, d):
        return cls(**d)