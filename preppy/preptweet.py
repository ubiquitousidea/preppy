"""
Whereas previously the TweetList contained Status objects,
now it will contain PrepTweet objects which each contain
a Status object as well as other types of metadata objects
to reflect the id_string-first data organization structure.
The effect of this should be that the session files (*.json) use
tweet ID string as their primary key - instead of current format (II)
which uses primary keys "metadata" and "tweets".
"""

import os
from numpy import array, zeros
from twitter import Status
from preppy.misc import read_json, ReverseLookup
from preppy.metadata import MetaData


# Clean this up. Should you really enforce that state_codes.json be in this dir?
dir_name = os.path.dirname(__file__)
d = read_json("{:}/state_codes.json".format(dir_name))
valid_state_codes = d["valid_state_codes"]
regions = ReverseLookup(d["regions"])


class PrepTweet(object):
    def __init__(self, status, metadata=None, **kwargs):
        """
        A class to wrap twitter.Status objects up with
        customizable metadata objects
        :param status: Status or dict returned by Status.AsDict()
        :param metadata: MetaData or dict returned by MetaData.as_dict
        """

        if isinstance(status, Status):
            self.status = status
        elif isinstance(status, dict):
            self.status = Status(**status)

        if metadata is None:
            self.metadata = MetaData()
        elif isinstance(metadata, MetaData):
            self.metadata = metadata
        elif isinstance(metadata, dict):
            self.metadata = MetaData.from_dict(metadata)

        self.MISSING = self.metadata.MISSING

        for k, v in kwargs.items():
            # set attributes for whatever else you want using keyword args
            setattr(self, k.lower(), v)

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

    def has_been_coded_for(self, vname):
        """
        Has this tweet been coded for XYZ?
        :param vname: name of the variable
        :return: BoolType
        """
        return self.metadata.has_been_coded_for(vname)

    @property
    def is_relevant(self):
        """
        Determine, by some means, if if the tweet is relevant to the search terms
        :return:
        """
        return self.metadata.is_relevant

    @property
    def id_str(self):
        """
        Return the unique ID string of the Tweet
        :return: str
        """
        return self.status.id_str

    @property
    def id(self):
        """
        Return the unique ID (integer) of the Tweet
        :return: int
        """
        return self.status.id

    @property
    def date(self):
        """
        Return the date that the tweet was created
        :return: str (see DATETIME_FORMATS["TWITTER"])
        """
        try:
            return self.status.created_at
        except AttributeError:
            return self.MISSING

    @property
    def user_id(self):
        """
        Get the unique ID number of the user who tweeted this tweet
        :return: int
        """
        try:
            return self.status.user["id"]
        except:
            return self.MISSING

    @property
    def user_id_str(self):
        """
        Get the unique ID number (as a string) of the user who tweeted
        :return:
        """
        try:
            return str(self.status.user['id'])
        except:
            return self.MISSING

    @property
    def hashtags(self):
        """
        Return a list of hashtags used in the text of the tweet
        :return: list
        """
        try:
            return [tag["text"] for tag in self.status.hashtags]
        except:
            return self.MISSING

    @property
    def hashtags_as_stringlist(self):
        """
        Return a formatted text string with all the hashtags separated by commas
        :return: str
        """
        tags = self.hashtags
        try:
            return ",".join(tags)
        except:
            return self.MISSING

    @property
    def text(self):
        """
        Return the text of the tweet
        Prefers long text; property will return short text
            if that is the only thing available.
        :return: str (may contain nuts, unicode emoticons)
        """
        try:
            if self.status.full_text:
                return self.status.full_text
            elif self.status.text:
                return self.text
            else:
                return self.MISSING
        except:
            return self.MISSING

    @property
    def words(self):
        """
        Return the words in the text of the tweet as a list
        Text string will be split on whitespace.
        :return: list of strings
        """
        try:
            return self.text.split()
        except:
            return self.MISSING

    @property
    def place(self):
        """
        Return the place where a mobile twitter user was when they tweeted.
            (If available)
        :return: str
        """
        try:
            return self.status.place["full_name"]
        except:
            return self.MISSING

    @property
    def coordinates(self):
        """
        Return the GPS coordinates of the tweet.

        These coordinates were encoded by the mobile twitter user's
        mobile device at the time of twitter use.

        Be careful to note that the coordinates listed as the corners of the
        bounding box under status.place['bounding_box']['coordinates'] are
        in the format [lat, lng];

        :return: list of floats [lat, lng]
        """
        try:
            bounding_box = array(
                self.status.place
                ["bounding_box"]
                ["coordinates"]
            ).squeeze()
            centroid = bounding_box.mean(axis=0)
            return centroid
        except:
            return zeros(2)

    @property
    def latitude(self):
        """
        Get the latitude from the coordinates attribute of the Status object
        which is stored as dict {'coordinates': [lng, lat], "type": "Point"}
        This information is only available when user had geotagging enabled
        on their mobile device.
        :return: float; latitude
        """
        try:
            return self.coordinates[0]
        except:
            return self.MISSING

    @property
    def longitude(self):
        """
        Get the longitude from the coordinates attribute of the Status object
        which is stored as dict {'coordinates': [lng, lat], "type": "Point"}
        This information is only available when user had geotagging enabled
        on their mobile device.
        :return: float; longitude
        """
        try:
            return self.coordinates[1]
        except:
            return self.MISSING

    @property
    def country(self):
        """
        Return the country from which the tweet originates
        :return: str
        """
        try:
            return self.status.place['country']
        except:
            return self.MISSING

    @property
    def state(self):
        """
        Return the US state from which the tweet was sent.
        :return: str
        """
        state_code = self.MISSING
        try:
            country_code = self.status.place["country_code"]
        except TypeError:
            return self.MISSING
        place_type = self.status.place["place_type"]
        if country_code == "US" and place_type == "city":
            full_name = self.status.place["full_name"]
            state_code = full_name.split(",")[-1].strip().upper()
            state_code = state_code if state_code in valid_state_codes else self.MISSING
        else:
            pass
        return state_code

    @property
    def region(self):
        """
        Get the region of the US a tweet originated from
        """
        try:
            return regions.lookup(self.state)
        except:
            return self.MISSING

    @property
    def user_place(self):
        """
        Get the place that the user identifies as location in their profile.
        :return: str
        """
        try:
            place = self.status.user['location']
            return place
        except:
            return self.MISSING

    @property
    def has_geotag(self):
        """
        Say whether or not this tweet has been geotagged and can be located on a map
        :return: BoolType (True/False)
        """
        place = self.place
        return place is not None
