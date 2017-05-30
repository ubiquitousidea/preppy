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
    a = config["A"]
    b = config["B"]
    c = config["C"]
    d = config["D"]
    return Api(a, b, c, d)


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

def unique_keys(_list):
    """
    Return the unique keys in dictionaries
        contained in a list of dictionaries
    :param _list: list of dictionaries
    :return: dict_keys object
    """
