"""
Whereas previously the TweetList contained Status objects,
now it will contain PrepTweet objects which each contain
a Status object as well as other types of metadata objects
to reflect the id_string-first data organization structure.
The effect of this should be that the session files (*.json) use
tweet ID string as their primary key - instead of current format (II)
which uses primary keys "metadata" and "tweets".
"""

from twitter import Status
from preppy.metadata import MetaData


class PrepTweet(object):
    def __init__(self, status, metadata, **kwargs):
        """
        A class to wrap twitter.Status objects up with
        customizable metadata objects
        :param status: dict returned by twitter.Status.AsDict()
        :param metadata: dict returned by preppy.MetaData.as_dict()
        """
        self.status = Status(**status)
        self.metadata = MetaData.from_dict(metadata)

    @property
    def as_dict(self):
        """
        Return a dictionary representation of this object
        :return: dict
        """
        return {"status": self.status.AsDict(),
                "metadata": self.metadata.as_dict}

    @classmethod
    def from_dict(cls, d):
        """
        Instantiate this class from a dictionary found in the session file
        for a particular tweet id string.
        :param d: dict returned by self.to_dict()
        :return:
        """
        assert "status" in d
        assert "metadata" in d
        return cls(**d)
