from twitter.api import Api
from twitter.models import Status
import json
import os
import shutil


DATE_FORMAT = "%Y-%M-%d"
CONFIG = "./config.json"


def get_api(config_file=CONFIG):
    """
    Instantiate a twitter.api.Api object
        from python-twitter package.
    :param str config_file: whether or not to
        authenticate using credentials
        stored in config.json
    :return: twitter.api.Api
    """
    with open(config_file, "r") as f:
        config = json.load(f)
    return Api(**config, sleep_on_rate_limit=True)


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
    d = None
    try:
        with open(fn, "r") as fh:
            d = json.load(fh)
    except:
        pass
    return d


def dict_to_tweets(iterable):
    pass


def anonymize(tweet):
    """
    Keep on certain aspects of the tweet: Place,
        Hashtag Content, Date, and Text
    :param twitter.models.Status tweet: A tweet
    :return: twitter.models.Status instance
    """
    assert isinstance(tweet, Status)
    tweet = tweet.AsDict()
    items_to_keep = ("place", "hashtags",
                     "text", "created_at",
                     "id_str")
    output = {}
    for item in items_to_keep:
        if item in tweet:
            output.update({
                item: tweet[item]
            })
    return Status(**output)


def minidate(dt, fmt=DATE_FORMAT):
    """
    Convert a datetime object into a string
        Save some lines of code because
        you love neat-looking-code.
    :param str fmt: Date formatting string
            Default is YYYY-MM-DD (compatible with twitter API)
            This arg is interpreted by strftime()
    :param datetime.Datetime dt: Date time object
    :return: String formatted nicely for
        Twitter, by default.
    """
    return dt.strftime(fmt)