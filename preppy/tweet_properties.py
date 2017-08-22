# Functions to extract certain types of information from the tweets

import os
from twitter import Status
from numpy import array, zeros
from preppy.misc import MISSING, read_json

missing = MISSING
dir_name = os.path.dirname(__file__)
d = read_json("{:}/state_codes.json".format(dir_name))
valid_state_codes = d["valid_state_codes"]


def get_id(tweet):
    return tweet.id


def get_date(tweet):
    return tweet.created_at


def get_user_id(tweet):
    try:
        return tweet.user.id
    except:
        return missing


def get_text(tweet):
    try:
        if tweet.full_text:
            return tweet.full_text
        elif tweet.text:
            return tweet.text
        else:
            return missing
    except:
        return missing


def get_place(tweet):
    try:
        return tweet.place["full_name"]
    except:
        return missing


def get_centroid(tweet):
    try:
        bounding_box = array(
            tweet.place
            ["bounding_box"]
            ["coordinates"]
        ).squeeze()
        centroid = bounding_box.mean(axis=0)
        return centroid
    except:
        return zeros(2)


def get_longitude(tweet):
    try:
        centroid = get_centroid(tweet)
        return centroid[0]
    except:
        return missing


def get_latitude(tweet):
    try:
        centroid = get_centroid(tweet)
        return centroid[1]
    except:
        return missing


def get_country(tweet):
    assert isinstance(tweet, Status)
    try:
        return tweet.place["country"]
    except:
        return missing


def get_state(tweet):
    """
    Get the state in which the tweet originated
    Currently relies upon the JSON response from twitter API
    Consider future use of Google reverse geocoding API

    Information page:
    https://developers.google.com/maps/documentation/geocoding/start

    Example:
    https://maps.googleapis.com/maps/api/geocode/json?latlng=40.714224,-73.961452&key=...

    :param tweet:
    :return:
    """
    assert isinstance(tweet, Status)
    state_code = missing
    try:
        country_code = tweet.place["country_code"]
    except TypeError:
        return missing
    place_type = tweet.place["place_type"]
    if country_code == "US" and place_type == "city":
        full_name = tweet.place["full_name"]
        state_code = full_name.split(",")[-1].strip().upper()
        state_code = state_code if state_code in valid_state_codes else missing
    else:
        pass
    return state_code


def get_region(tweet):
    """
    Get the region of the US a tweet originated from
    :param tweet:
    :return:
    """
    return missing


def get_user_place(tweet):
    try:
        place = tweet.user.location
        return place
    except:
        return missing


