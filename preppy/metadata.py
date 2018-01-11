from numpy import mean
from preppy.misc import CodeBook, MISSING, get_logger


CODE_BOOK = CodeBook.from_json('codebook.json')
logger = get_logger(__file__)


class MetaData(object):
    def __init__(self, **kwargs):
        """
        An object to represent the metadata we encode about a particular tweet
        This can include judgements about the tweet like relevance or
        derived metadata such as GPS coordinates derived from place listed in user profile
        """

        self.relevance = {}
        self.sentiment = {}
        self.location = {}
        self.user_place_coordinates = {}
        for attribute, value in kwargs.items():
            setattr(self, attribute.lower(), value)

    def variable_names(self):
        return self.__dict__.keys()

    def record(self, param, user_id, value):
        """
        Record a piece of metadata in this object
        :param param: name of the variable to be recorded
        :param user_id: name of the user who coded this varible
        :param value: the value that they coded
        :return: NoneType
        """
        param_dict = getattr(self, param.lower())
        param_dict.update(
            {
                user_id: value
            }
        )
        setattr(self, param.lower(), param_dict)

    def lookup(self, param):
        """
        Get the average value for this parameter
        Average taken over all users who coded for this variable
        :param param: the variable in question
        :return: the average value for that variable
        """
        user_dict = getattr(self, param.lower())
        numerical_values = [float(val) for val in user_dict.values()]
        return mean(numerical_values)

    def has_been_coded_for(self, param):
        """
        Say whether or not a given variable has been coded by at least one person
        :param param: variable name that may have been coded
        :return: BoolType (True/False)
        """
        return len(getattr(self, param.lower())) != 0

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
            return MISSING

    @property
    def as_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d):
        if d is not None:
            return cls(**d)
        else:
            return cls()
