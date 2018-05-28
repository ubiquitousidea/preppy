"""A module for text analytics through IBM Watson

A formerly standalone utility currently being worked into preppy 

Inputs: a preppy json file of tweets coded as relevant.
Outputs: appends subdict within a tweet dict called 'nlu',
         contains Watsons NLU output for the tweet. 
"""

import watson_developer_cloud
import json

class Watson(object):
    """Base class to interface preppy with watson_developer_cloud"""
    def __init__(self, config_file):
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
            version=self.creds.get('version'))
        return api

    def analyze(self, *args, **kwargs):
        result = self.api.analyze(*args, **kwargs)
        return result


def read_ids(id_file):
    """Get IDs of tweets classified as relevant by keyword_classify.R 
    Assumes a .csv file with one column and one column header"""

    with open(id_file) as f:
        ids = f.read().replace('"', '').splitlines()
    return ids[1:]
