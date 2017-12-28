from numpy import mean


class MetaData(object):

    MISSING = None

    def __init__(self, **kwargs):
        """
        An object to represent the metadata we encode about a particular tweet
        This can include judgements about the tweet like relevance or
        derived metadata such as GPS coordinates derived from place listed in user profile
        """

        self.relevance = {}
        self.sentiment = {}
        self.location = {}
        for attribute, value in kwargs.items():
            setattr(self, attribute.lower(), value)

    @property
    def is_relevant(self):
        """
        return the average of encoded relevance
        :return: float
        """
        values = list(
            self.relevance.values()
        )
        if len(values) > 0:
            return mean(
                [float(val)
                 for val
                 in values]
            )
        else:
            return self.MISSING

    @property
    def as_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d):
        return cls(**d)
