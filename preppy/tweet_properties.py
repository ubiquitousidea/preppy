# Functions to extract certain types of information from the tweets

import os
from twitter import Status
from numpy import array, zeros
from preppy.misc import MISSING, read_json, ReverseLookup


missing = MISSING
dir_name = os.path.dirname(__file__)
d = read_json("{:}/state_codes.json".format(dir_name))
valid_state_codes = d["valid_state_codes"]
regions = ReverseLookup(d["regions"])


def get_id(tweet, *args):
    return tweet.id


def get_id_str(tweet, *args):
    return tweet.id_str


def get_date(tweet, *args):
    return tweet.created_at


def get_user_id(tweet, *args):
    try:
        return tweet.user['id']
    except:
        return missing


def get_hashtags(tweet, *args):
    """
    Return a list of the hashtag texts
    """
    try:
        return [tag["text"] for tag in tweet.hashtags]
    except:
        return missing


def get_hashtag_stringlist(tweet, *args):
    """
    Careful putting this into a csv file since this
    return is a string that contains commas
    """
    tags = get_hashtags(tweet)
    if tags:
        return ",".join(tags)
    else:
        return missing


def get_text(tweet, *args):
    try:
        if tweet.full_text:
            return tweet.full_text
        elif tweet.text:
            return tweet.text
        else:
            return missing
    except:
        return missing


def get_place(tweet, *args):
    try:
        return tweet.place["full_name"]
    except:
        return missing


def get_centroid(tweet, *args):
    """
    Get the centroid of the geotag bounding box
    Note that twitter uses (latitude/longitude) instead
        of the usual (longitude/latitude)
    """
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


def get_longitude(tweet, *args):
    try:
        centroid = get_centroid(tweet)
        return centroid[0]
    except:
        return missing


def get_latitude(tweet, *args):
    try:
        centroid = get_centroid(tweet)
        return centroid[1]
    except:
        return missing


def get_country(tweet, *args):
    assert isinstance(tweet, Status)
    try:
        return tweet.place["country"]
    except:
        return missing


def get_state(tweet, *args):
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


def get_region(tweet, *args):
    """
    Get the region of the US a tweet originated from
    :param tweet: twitter.Status object
    :return:
    """
    try:
        state_code = get_state(tweet)
        return regions.lookup(state_code)
    except:
        return missing


def get_user_place(tweet, *args):
    try:
        place = tweet.user['location']
        return place
    except:
        return missing


def get_coordinates(tweet, *args):
    """
    Return the coordinates attribute of the tweet.
    Coordinates maybe here or inside the place attribute.
    :param tweet: twitter.Status instance
    :param args: extra arguments that will be ignored
    :return: Coordinates
    """
    try:
        return tweet.coordinates
    except:
        return missing


def get_geo(tweet, *args):
    """
    Return the geo attribute of the tweet
    """
    try:
        return tweet.geo
    except:
        return missing


def is_relevant(tweet, tweet_list):
    return tweet_list.get_metadata(tweet.id_str, "RELEVANCE")


def get_words(tweet, *args):
    """
    Return set of words in a tweet text
    :param tweet: twitter.Status instance
    :return: set
    """
    return {}


def has_geotag(tweet, *args):
    place = get_place(tweet)
    coord = get_coordinates(tweet)
    geooo = get_geo(tweet)
    geotagged = \
        place is not None or \
        coord is not None or \
        geooo is not None
    return geotagged


def has_user_place_or_geotag(tweet, *args):
    hasgeotag = has_geotag(tweet)
    hasuserplace = get_user_place(tweet) is not None
    return hasgeotag or hasuserplace
