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
from preppy.misc import (
    read_json, ReverseLookup, MISSING,
    get_logger, warn_of_error, silence_errors_return_nothing)
from preppy.metadata import MetaData


logger = get_logger(__file__)


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
            self.status = Status(**status)

        if metadata is None:
            self.metadata = MetaData()
        elif isinstance(metadata, MetaData):
            self.metadata = metadata
        elif isinstance(metadata, dict):
            self.metadata = MetaData.from_dict(metadata)

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

    def has_been_coded_by(self, vname, coder):
        """
        Say whether or not a given variable has been coded by a specific person/utility
        :param vname: the variable name that may have been coded
        :param coder_name: the coder of interest
        :return: BoolType
        """
        return self.metadata.has_been_coded_by(vname, coder)

    def lookup(self, variable_name):
        try:
            return self.metadata.lookup(variable_name)
        except AttributeError as e:
            e.message = "Unknown PrepTweet attribute {}".format(variable_name)
            raise e

    @property
    @silence_errors_return_nothing
    def is_relevant(self):
        """
        Return the average of all user encoded relevance scores
        :return:
        """
        return self.metadata.is_relevant

    @property
    def keyword_relevant(self):
        """
        Determine if the tweet was coded as relevant by keyword_classify.R
        :return: BoolType
        """
        return self.metadata.keyword_relevant

    @property
    @silence_errors_return_nothing
    def relevance(self):
        """
        Determine, by some means, if if the tweet is relevant to the search terms
        :return: dictionary of relevance
        """
        return self.metadata.relevance

    @property
    @silence_errors_return_nothing
    def id_str(self):
        """
        Return the unique ID string of the Tweet
        :return: str
        """
        return self.status.id_str

    @property
    @silence_errors_return_nothing
    def id(self):
        """
        Return the unique ID (integer) of the Tweet
        :return: int
        """
        return self.status.id

    @property
    @silence_errors_return_nothing
    def date(self):
        """
        Return the date that the tweet was created
        :return: str (see DATETIME_FORMATS["TWITTER"])
        """
        return self.status.created_at

    @property
    @silence_errors_return_nothing
    def user_id(self):
        """
        Get the unique ID number of the user who tweeted this tweet
        :return: int
        """
        return self.status.user["id"]

    @property
    @silence_errors_return_nothing
    def user_id_str(self):
        """
        Get the unique ID number (as a string) of the user who tweeted
        :return:
        """
        return str(self.status.user['id'])

    @property
    @silence_errors_return_nothing
    def hashtags(self):
        """
        Return a list of hashtags used in the text of the tweet
        :return: list
        """
        return [tag["text"] for tag in self.status.hashtags]

    @property
    @silence_errors_return_nothing
    def hashtags_as_stringlist(self):
        """
        Return a formatted text string with all the hashtags separated by commas
        :return: str
        """
        tags = self.hashtags
        return ",".join(tags)

    @property
    @silence_errors_return_nothing
    def text(self):
        """
        Return the text of the tweet
        Prefers long text; property will return short text
            if that is the only thing available.
        :return: str (may contain nuts, unicode emoticons)
        """

        if self.status.full_text:
            return self.status.full_text
        elif self.status.text:
            return self.text
        else:
            return MISSING

    @property
    @silence_errors_return_nothing
    def words(self):
        """
        Return the words in the text of the tweet as a list
        Text string will be split on whitespace.
        :return: list of strings
        """
        return self.text.split()

    @property
    @silence_errors_return_nothing
    def place(self):
        """
        Return the place where a mobile twitter user was when they tweeted.
            (If available)
        :return: str
        """
        return self.status.place["full_name"]

    @property
    def coordinates(self):
        """
        Return the GPS coordinates of the tweet.
        These coordinates are obtained in one of two ways
        1 (Preferred):
            These coordinates were encoded by the mobile twitter user's
            mobile device at the time of twitter use.
        2 (If 1 is not available)
            Look for user place coordinates in the metadata
            These would have been encoded by the PlaceInfo class
            which uses Google Geocoding API.
        3 Else
            Return south pole (0,0)
        Be careful to note that the coordinates listed as the corners of the
        bounding box under status.place['bounding_box']['coordinates'] are
        in the format [lat, lng];

        :return: list of floats [lat, lng]
        """
        # TODO: Add the feature where coordinates come from multiple sources.
        # Consider whether or not you'd want to output the categorical
        # variable indicating the source of the coordinate data or
        # make the user place coordinates a different property entirely.
        try:
            bounding_box = array(
                self.status.place
                ["bounding_box"]
                ["coordinates"]
            ).squeeze()
            centroid = bounding_box.mean(axis=0)
            return centroid
        except AttributeError:
            return zeros(2)

    @property
    @silence_errors_return_nothing
    def latitude(self):
        """
        Get the latitude from the coordinates attribute of the Status object
        which is stored as dict {'coordinates': [lng, lat], "type": "Point"}
        This information is only available when user had geotagging enabled
        on their mobile device.
        :return: float; latitude
        """
        return self.coordinates[0]

    @property
    @silence_errors_return_nothing
    def longitude(self):
        """
        Get the longitude from the coordinates attribute of the Status object
        which is stored as dict {'coordinates': [lng, lat], "type": "Point"}
        This information is only available when user had geotagging enabled
        on their mobile device.
        :return: float; longitude
        """
        return self.coordinates[1]

    @property
    @silence_errors_return_nothing
    def country(self):
        """
        Return the country from which the tweet originates
        :return: str
        """
        return self.status.place['country']

    @property
    def state(self):
        """
        Return the US state from which the tweet was sent.
        :return: str
        """
        state_code = MISSING
        try:
            country_code = self.status.place["country_code"]
        except TypeError:
            return MISSING
        place_type = self.status.place["place_type"]
        if country_code == "US" and place_type == "city":
            full_name = self.status.place["full_name"]
            state_code = full_name.split(",")[-1].strip().upper()
            state_code = state_code if state_code in valid_state_codes else MISSING
        else:
            pass
        return state_code

    @property
    def city(self):
        """
        Return the city associated with this tweet.

        :return: str
        """

        try:
            city = self.status.place["full_name"].strip(r",[A-Z ]")
        except TypeError:
            city = None
        if not city:
            try:
                city = self.metadata.as_dict.get("user_city").get("google_geocoding")
            except (TypeError, AttributeError):
                city = None
        return city


    @property
    @silence_errors_return_nothing
    def region(self):
        """
        Get the region of the US a tweet originated from
        """
        return regions.lookup(self.state)

    @property
    @silence_errors_return_nothing
    def user_place(self):
        """
        Get the place that the user identifies as location in their profile.
        :return: str
        """
        place = self.status.user['location']
        return place

    @property
    @silence_errors_return_nothing
    def has_geotag(self):
        """
        Say whether or not this tweet has been geotagged and can be located on a map
        :return: BoolType (True/False)
        """
        place = self.place
        # TODO: Add the feature where it considers a tweet to be geotagged
        # if the user place coordinates have been encoded by PlaceInfo().
        # user_coords = self.metadata.user_place_coordinates
        return place is not None

    @property
    def has_nlu(self):
        """
        This and the methods defined below are a bit of a mess, we need a proper class to store watson output
        :return: BoolType
        """
        return self.metadata.has_been_coded_for("nlu")

    @property
    def sentiment(self):
        """
        :return: dict
        """
        if self.metadata.as_dict['nlu'].get('watson_nlu') is not None:
            return self.metadata.as_dict['nlu']['watson_nlu']['sentiment']
        else:
            return None

    @property
    def doc_sentiment_score(self):
        if self.sentiment:
            return self.sentiment['document']['score']
        else:
            return None

    @property
    def doc_sentiment_lab(self):
        if self.sentiment:
            return self.sentiment['document']['label']
        else:
            return None

    @property
    def doc_emotion(self):
        return self.metadata.as_dict['emotion'].get('document')['emotion']

    @property
    def doc_anger(self):
        return self.doc_emotion.get('anger')

    @property
    def doc_disgust(self):
        return self.doc_emotion.get('disgust')

    @property
    def doc_fear(self):
        return self.doc_emotion.get('fear')

    @property
    def doc_joy(self):
        return self.doc_emotion.get('joy')
    @property
    def doc_sadness(self):
        return self.doc_emotion.get('sadness')
