from twitter.api import Api
from twitter.models import Status
import json
import os
import shutil


def get_api(auth=True):
    """
    Instantiate a twitter.api.Api object
        from python-twitter package.
    :param BoolType auth: whether or not to
        authenticate using credentials
        stored in config.json
    :return: twitter.api.Api
    """
    if auth:
        with open("./config.json", "r") as f:
            config = json.load(f)
    else:
        config = {}
    return Api(**config)


def write_json(_dict, fn, pretty=True):
    """
    Write a dictionary to a file
    :param dict _dict: dictionary of interest
    :param str fn: file name to be written
    :return: NoneType
    """
    kwargs = {"indent": 4,
              "sort_keys": True} if pretty else {}
    fn_tmp = temp_file_name(fn)
    with open(fn_tmp, "w") as fh:
        output = json.dumps(_dict, **kwargs)
        fh.write(output)
    shutil.move(fn_tmp, fn)
    os.remove(fn_tmp)


def temp_file_name(_fn):
    """
    Make a file name into a temp file name
    :param str _fn: file name
    :return: str
    """
    root, ext = os.path.splitext(_fn)
    return root + '.tmp'


def read_json(fn=None):
    """
    Read json file and return a dictionary
    :param fn: file name string
    :return: dict
    """
    if not fn:
        return None
    with open(fn, "r") as fh:
        d = json.load(fh)
    return d


def write_tweet_list(tweetlist, fname=None):
    """
    Write out a list of tweets
    :param tweetlist: list of twitter.models.Status objects
    :param fname: file name of the tweet list file
    :return: NoneType
    """
    try:
        fname = fname if fname else 'tweets.json'
        tweetlist = [anonymize(tweet) for tweet in tweetlist]
        write_json({"TWEETS": tweetlist}, fname)
    except:
        raise ValueError("Unable to write tweet list to json file")


def anonymize(tweet):
    """
    Remove user id from tweet dictionary to comply with
        user agreement that no use data is cached with
        location data.
    :param tweet: dictionary or twitter.models.Status
    :return: twitter.models.Status instance
    """
    if isinstance(tweet, Status):
        tweet = tweet.AsDict()
    assert isinstance(tweet, dict)
    items = ("user",
             "retweeted_status",
             "user_mentions",
             "in_reply_to_screen_name",
             "in_reply_to_user_id")
    for item in items:
        if item in tweet:
            del tweet[item]
    return Status(**tweet)


def unique_keys(_list):
    """
    Return the unique keys in dictionaries
        contained in a list of dictionaries
    :param _list: list of dictionaries
    :return: dict_keys object
    """
    ukeys = set()
    for item in _list:
        some_keys = set(item.keys())
        ukeys.update(some_keys)
    return sorted(list(ukeys))