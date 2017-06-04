from twitter.api import Api
from twitter.models import Status
import json
import os
import shutil


DATE_FORMAT = "%Y-%M-%d"


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


def anonymize(tweet):
    """
    Remove user id from tweet dictionary to comply with
        user agreement that no use data is cached with
        location data.
    :param twitter.models.Status tweet: A tweet
    :return: twitter.models.Status instance
    """
    assert isinstance(tweet, Status)
    tweet = tweet.AsDict()
    items = ("user",
             "retweeted_status",
             "user_mentions",
             "in_reply_to_screen_name",
             "in_reply_to_user_id")
    for item in items:
        if item in tweet:
            del tweet[item]
    return Status(**tweet)


def minidate(dt, fmt=DATE_FORMAT):
    """
    Convert a datetime object into a string
        Save some lines of code because
        you love neat-looking-code.
    :param str fmt: format string for strftime()
    :param datetime.Datetime dt: Date time object
    :return: String formatted nicely for
        Twitter, by default.
    """
    return dt.strftime(fmt)