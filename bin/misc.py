from twitter.api import Api
import json
import time
import shutil
import os
import uuid
from contextlib import contextmanager


DATE_FORMAT = "%Y-%m-%d"
CONFIG = "./config.json"
SESSION_FILE_NAME = "preppy_session.json"


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


def backup_session(destination_dir, file_name):
    """
    Copy the latest session file into the
        backup directory and rename with
        sequentially id
    :param destination_dir: the directory into which the
        backed up session file will be placed
    :param file_name: path to file
    :return:
    """
    if not os.path.isfile(file_name):
        raise IOError("Could not find file named {:s}".format(file_name))
    if not os.path.isdir(destination_dir):
        os.mkdir(destination_dir)
    basename, extension = os.path.splitext(file_name)
    uid = "_" + str(uuid.uuid1())
    destination = os.path.join(destination_dir, basename + uid + extension)
    shutil.copy(file_name, destination)


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
