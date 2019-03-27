"""A module for text analytics through IBM Watson

A formerly standalone utility currently being worked into preppy 

Inputs: a preppy json file of tweets coded as relevant.
Outputs: appends subdict within a tweet dict called 'nlu',
         contains Watsons NLU output for the tweet. 
"""

from watson_developer_cloud import NaturalLanguageUnderstandingV1 as nlu
from watson_developer_cloud.natural_language_understanding_v1 import (
    Features, KeywordsOptions, EntitiesOptions
)
import argparse
from preppy.misc import (read_json, write_json)
import yaml


class Watson(object):
    """Base class to interface preppy with watson_developer_cloud"""
    def __init__(self, config_file):
        self.creds = self._parse_credentials(config_file)
        self.api = self._get_api()

    @staticmethod
    def _parse_credentials(credential_file):
        """
        Parse the configuration file that contains API keys
        :param credential_file: name of the yaml file
        :return: dict
        """
        with open(credential_file) as f:
            creds = yaml.load(f)
        return creds

    def _get_api(self):
        raise NotImplementedError()


class NLU(Watson):
    """Interface to Watson's Natural Language Understanding service"""
    def __init__(self, *args, **kwargs):
        Watson.__init__(self, *args, **kwargs)

    def _get_api(self):
        key = self.creds.get("NATURAL_LANGUAGE_UNDERSTANDING_APIKEY")
        url = self.creds.get("NATURAL_LANGUAGE_UNDERSTANDING_URL")
        api = nlu(version="2018-11-16",
                  iam_apikey=key,
                  url=url)
        return api

    def analyze(self, text):
        ft = Features(entities=EntitiesOptions(),
                      keywords=KeywordsOptions())
        return self.api.analyze(text=text, features=ft).get_result()


def read_ids(id_file):
    """Get IDs of tweets classified as relevant by keyword_classify.R 
    Assumes a .csv file with one column and one column header"""

    with open(id_file) as f:
        ids = f.read().replace('"', '').splitlines()
    return ids[1:]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-session", "--session", required = True)
    parser.add_argument("-config", "--config", required = True)
    parser.add_argument("-idfile", "--idfile", required = True)
    return parser.parse_args()


def main():
    """Procedural code remains here until integrated with preppy application logic"""
    args = parse_args()
    session_file = args.session
    config_file = args.config
    id_file = args.idfile
    relevant_ids = read_ids(id_file)
    tweets = read_json(session_file)
    nlu = NLU(config_file)
    for k in tweets.keys():
        if k in relevant_ids:
            tweet_text = tweets[k]['status']['full_text']
            print("Analyzing tweet %s" % k)
            tweets[k]['nlu'] = nlu.analyze(tweet_text)
    write_json(session_file, fn="preppy_session.json")


if __name__ == '__main__':
    main()
