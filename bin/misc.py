from twitter.api import Api
from twitter.models import Status
import json


def get_api():
    """
    Instantiate a twitter.api.Api object
        from python-twitter package.
    :return: twitter.api.Api
    """
    with open("./config.json", "r") as f:
        config = json.load(f)
    return Api(**config)


def write_json(_dict, fn):
    """
    Write a dictionary to a file
    :param dict _dict: dictionary of interest
    :param str fn: file name to be written
    :return: NoneType
    """
    with open(fn, "w") as fh:
        fh.write(
            json.dumps(
                _dict, indent=4,
                sort_keys=True
            )
        )


def write_tweet_list(tweetlist, fname=None):
    """
    Write out a list of tweets
    :param tweetlist: list of twitter.models.Status objects
    :param fname: file name of the tweet list file
    :return: NoneType
    """
    try:
        fname = fname if fname else 'tweets.json'
        tweetlist = [tweet.AsDict() for tweet in tweetlist]
        write_json({"TWEETS": tweetlist}, fname)
    except:
        raise ValueError("Unable to write tweet list to json file")


def unique_keys(_list):
    """
    Return the unique keys in dictionaries
        contained in a list of dictionaries
    :param _list: list of dictionaries
    :return: dict_keys object
    """
    ukeys = set()
    for item in _list:
        ukeys.update(item.keys())
    return sorted(list(ukeys))