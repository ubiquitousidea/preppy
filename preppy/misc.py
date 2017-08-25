import os
import time
import json
import shutil
import logging
import datetime
import itertools
from twitter import Status
from twitter.api import Api
from contextlib import contextmanager

MISSING = None
SESSION_FILE_NAME = "preppy_session.json"
now = datetime.datetime.now
DT_FORMATS = {
    "TWITTER": "%Y-%m-%d",
    "BACKUPS": "%Y_%m_%d_%H_%M_%S_%f"
}


class CodeBook:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            logging.debug("Loading {:} into CodeBook".format(key))
            self.__setattr__(key, value)

    def explain_possible_values(self, variable_name):
        """
        Return the dictionary explaining the possible values
        and their meanings for a given variable in the Code Book
        :param variable_name: which variable
        :return: dict
        """
        try:
            return self.__getattribute__(variable_name)
        except AttributeError:
            available = ",".join(self.variable_names)
            msg = \
                "{:} not found in Code Book. Possible values are {:}" \
                .format(variable_name, available)
            raise AttributeError(msg)

    @classmethod
    def from_json(cls, file_name=None):
        if file_name is None:
            file_name = "codebook.json"
        d = read_json(file_name)
        return cls(**d)

    @property
    def variable_names(self):
        output = list(self.__dict__.keys())
        output.sort()
        return output

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


class ReverseLookup(object):
    """
    Given some dictionary of the form {key: list,...},
    find the key whose (list) value contains a value
    """
    def __init__(self, d):
        self._lookup = {}
        assert isinstance(d, dict)
        for key, listvalue in d.items():
            self._lookup.update(
                {
                    item: key
                    for item
                    in listvalue
                }
            )

    @classmethod
    def from_json(cls, json_name, primary_key=None):
        d = read_json(json_name)
        if primary_key:
            d = d[primary_key]
        return cls(d)

    def lookup(self, value):
        return self._lookup[value]


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


def enforce_extension(file_name, ext):
    """
    Enforce that a file name has a certain extension
    :param file_name: the prior file name
    :param ext: the desired extension for that file.
    :return: a new file name
    """
    ext = ext.strip()
    if ext[0] != '.':
        ext = "." + ext
    basename, _ = os.path.splitext(file_name)
    return basename + ext


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
    logging.debug("Returning tweet \'full_text\' attribute")
    return tweet.full_text


def ask_param(param_name, tweet, api=None):
    """
    Print the text of a tweet
    and ask the user to input the sentiment they
    believe the tweet's text has
    :param param_name: The name of the parameter to ask about
        (Only affects the question posed to the user)
    :param tweet: the tweet object
    :param api: Optional. A twitter.Api instance for
        web based retrieval of the tweet text
    :return:
    """
    assert isinstance(tweet, Status)
    if api is not None:
        assert isinstance(api, Api)
    if hasattr(tweet, "full_text") and tweet.full_text is not None:
        logging.debug("Returning tweet \'full_text\' attribute")
        output = tweet.full_text
    elif hasattr(tweet, "text") and tweet.text is not None:
        logging.debug("Returning tweet \'text\' attribute")
        output = tweet.text
    else:
        logging.debug("Retrieving tweet from internet using Twitter API")
        output = get_text_from_api(tweet, api)
    print(output)
    print("What is the {:}? ".format(param_name.title()))
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
    logging.debug("Copied {:} to backups folder".format(file_name))


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


def grouper(n, iterable):
    """
    An iterable that breaks up another iterable into groups of size <= n.
    From stackoverflow
    https://stackoverflow.com/questions/8991506/iterate-an-iterator-by-chunks-of-n-in-python
    :param n: Chunk Size
    :param iterable: The iterable to be broken into chunks of size N
    """
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


def rehydrate_tweets(id_list, api):
    """
    Given a list of tweet ID strings (not integers),
        return a dict of tweets of the form
            {id_str: Status, ...}
    :param id_list: list of strings
    :param api: twitter.Api instance
    :return: dict of Status instances
        primary key: id_str
    """
    assert isinstance(api, Api)
    get_status_url = "https://api.twitter.com/1.1/statuses/lookup.json"
    api_calls = 0
    output = {}
    for _ids in grouper(100, id_list):
        data = {"id": ",".join(_ids)}
        assert isinstance(api, Api)
        rate_lim = api.CheckRateLimit(get_status_url)
        if rate_lim.remaining == 0:
            time.sleep(60*15)
        response = api._RequestUrl(
            get_status_url,
            verb="GET",
            data=data)
        print("Made Twitter API call")
        api_calls += 1
        for tweet_dict in response.json():
            tweet = Status.NewFromJsonDict(tweet_dict)
            print("Updated {:}".format(tweet.id_str))
            output.update({tweet.id_str: tweet})
    print("Made {:} API calls".format(api_calls))
    return output
