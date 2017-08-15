from twitter.api import Api
from twitter import Status
import json
import time
import shutil
import os
import datetime
from contextlib import contextmanager


MISSING = None

DT_FORMATS = {
    "TWITTER": "%Y-%m-%d",
    "BACKUPS": "%Y_%m_%d_%H_%M_%S_%f"
}


class CodeBook:
    def __init__(self):
        pass

    SENTIMENT = {
        "1": "Negative sentiment",
        "2": "Neutral sentiment",
        "3": "Positive sentiment"
    }

    def has_variable(self, var_name):
        try:
            _ = self.__getattribute__(var_name)
            return True
        except AttributeError:
            return False

    def possible_values(self, var_name):
        output = list(self.__getattribute__(var_name).keys())
        output.sort()
        return output


SESSION_FILE_NAME = "preppy_session.json"
now = datetime.datetime.now


@contextmanager
def cd(new_directory=None):
    """
    From Stack Exchange example
    https://stackoverflow.com/questions/431684/how-do-i-cd-in-python
    :param new_directory: Directory to change into
    """
    if new_directory is None:
        new_directory = "."
    previous_directory = os.getcwd()
    if not os.path.isdir(new_directory):
        os.mkdir(new_directory)
    new_directory = os.path.expanduser(new_directory)
    os.chdir(new_directory)
    try:
        yield
    finally:
        os.chdir(previous_directory)


def date_modified(file_path):
    try:
        return time.ctime(os.path.getmtime(file_path))
    except:
        return None


def cull_old_files(_dir=None, n_keep=10):
    """
    #--------------------------------------------------------- a warning --
    # - Warning, this function contains a call to os.remove(). ------------
    # --- Use with caution. -----------------------------------------------
    #----------------------------------------------------------------------
    Remove all but the 10 newest files in a directory
    :param _dir: Directory to cull
    :return: NoneType
    """
    with cd(_dir):
        file_list = os.listdir(".")
        file_list.sort(key=date_modified)
        files_to_cull = file_list[:-n_keep]  # Take all but the last 10 files
        for file_path in files_to_cull:
            os.remove(file_path)


def get_text_from_api(tweet, api):
    assert isinstance(tweet, Status)
    assert isinstance(api, Api)
    tweet = api.GetStatus(tweet.id)
    return tweet.full_text


def get_sentiment(tweet, api=None):
    """
    Print the text of a tweet
    and ask the user to input the sentiment they
    believe the tweet's text has
    Possible values are encoded by SENTIMENT_DICT
    :param tweet: the tweet object
    :param api: Optional. A twitter.Api instance for
        web based retrieval of the tweet text
    :return:
    """
    assert isinstance(tweet, Status)
    if api is not None:
        assert isinstance(api, Api)
    if hasattr(tweet, "full_text"):
        output = tweet.full_text
    elif hasattr(tweet, "text"):
        output = tweet.text
    else:
        output = get_text_from_api(tweet, api)
    print(output)
    print("What is the Sentiment? ")
    param = input()
    return str(param)


def backup_session(destination_dir, file_name):
    """
    Copy the latest session file into the
        backup directory and rename with
        sequential id
    :param destination_dir: the directory into which the
        backed up session file will be placed
    :param file_name: path to file
    :return:
    """
    if not os.path.isfile(file_name):
        msg = "Could not find file named {:s}"
        raise IOError(msg.format(file_name))
    if not os.path.isdir(destination_dir):
        os.mkdir(destination_dir)
    basename, extension = os.path.splitext(file_name)
    uid = "_" + date_string()
    destination = os.path.join(
        destination_dir,
        basename + uid + extension
    )
    shutil.copy(file_name, destination)


def date_string(fmt=None):
    """
    Return a string of numbers representing
    the date and time (to the microsecond)
    :param fmt: date time formatting string (see strftime)
    :return: str
    """
    if fmt is None:
        fmt = DT_FORMATS["BACKUPS"]
    return now().strftime(fmt)


def get_api(config_file):
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
    api = Api(sleep_on_rate_limit=True,
              tweet_mode='extended',
              **config)
    return api


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


def minidate(dt, fmt=DT_FORMATS["TWITTER"]):
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


def is_list(v):
    return isinstance(v, (list, tuple))


def make_list(v):
    """
    Make the argument into a list if it
    isn't already a list, then return it.
    """
    if is_list(v):
        return v
    else:
        return [v]
