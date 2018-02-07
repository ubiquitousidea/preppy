"""A module for text analytics through IBM Watson

A formerly standalone utility currently being worked into preppy 

Inputs: a preppy json file of tweets coded as relevant.
Outputs: appends subdict within a tweet dict called 'nlu',
         contains Watsons NLU output for the tweet. 
"""

import watson_developer_cloud
from watson_developer_cloud.natural_language_understanding_v1 import Features
from watson_developer_cloud.watson_developer_cloud_service import WatsonException

import argparse
from preppy.misc import (read_json, write_json)
import json

class Watson(object):
    """Base class to interface preppy with watson_developer_cloud"""
    def __init__(self, config_file, version):
        self.version = version
        self.creds = self._parse_config(config_file)
        self.api = self._get_api()

    def _parse_config(self, config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            creds = config.get("watson")
            return creds

    def _get_api(self):
        raise NotImplementedError()


class NLU(Watson):
    """Interface to Watson's Natural Language Understanding service"""
    def __init__(self, *args, **kwargs):
        Watson.__init__(self, *args, **kwargs)

    def _get_api(self):
        api = watson_developer_cloud.NaturalLanguageUnderstandingV1(
            username=self.creds.get('username'),
            password=self.creds.get('password'),
            version=self.version)
        return api

    def analyze(self, *args, **kwargs):
        result = self.api.analyze(*args, **kwargs)
        return result


def read_ids(id_file):
    """Get IDs of tweets classified as relevant by keyword_classify.R 
    Assumes a .csv file with one column and one column header"""

    with open(id_file) as f:
        ids = f.read().replace('"', '').splitlines()
    return ids[1::]


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
    watson = Watson(config_file)

    for k in tweets.keys():
        if k in relevant_ids:
            try:
                tweet_text = tweets[k]['status']['full_text']
                print("Analyzing tweet %s" % k)
                tweets[k]['nlu'] = watson.call_nlu(tweet_text)
            except WatsonException:
                print("WatsonException on %s" % k)
                tweets[k]['nlu'] = None
            except KeyError:
                print("KeyError on tweet %s" % k)
                tweets[k]['nlu'] = None
            except:
                print("Unknown error on tweet %s" % k)
                break

    # this should really be done by Preppy object
    write_json(session_file, fn="preppy_session.json")


if __name__ == '__main__':
    main()
