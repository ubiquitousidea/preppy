"""A module for text analytics through IBM Watson

Currently a standalone utility, to be worked into preppy. 

Inputs: a preppy json file of tweets coded as relevant.
Outputs: appends subdict within a tweet dict called 'nlu',
         contains Watsons NLU output for the tweet. 
"""

import watson_developer_cloud
import watson_developer_cloud.natural_language_understanding.features.v1 as features
import argparse
import json
import time

class Watson():
    """Handles communication with IBM Watson
    
    Currently only talks to NLU API, 
    Support for other watson APIs can be added should demand arise. 
    """
    
    def __init__(self, config_file):
        self.creds = self._parse_config(config_file)
        self.nlu = self._get_nlu()
    
    def _parse_config(self, config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
            creds = config.get("watson")
            return creds

    def _get_nlu(self):
        """Instantiates watson NLU api object using keys from config.json"""
        username = self.creds.get('username')
        password = self.creds.get('password')
        version = "2017-02-27"
        nlu = watson_developer_cloud.NaturalLanguageUnderstandingV1(
            username=username,
            password=password,
            version=version)
        return nlu

    def call_nlu(self, tweet):
        """Makes call to Watson NLU API"""
        result = self.nlu.analyze(
            text=tweet,
            features = [features.Concepts(), features.Keywords(), features.Emotion(), features.Sentiment()]
            )
        return result 

def parse_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("-tweetfile", "--tweetfile", required = True)
    parser.add_argument("-config", "--config", required = True)
    parser.add_argument("-relevant", "--relevant")
    return parser.parse_args()

def main():
    """Procedural code remains here until it finds a home in preppy application logic"""
    args = parse_args()
    tweetfile = args.tweetfile 
    config_file = args.config
    relevant_tweets = args.relevant

    with open(tweetfile) as f:
        tweets = json.load(f)
        watson = Watson(config_file)
        for k in tweets.keys():
            try:
                tweet_text = tweets[k]['full_text']
                print("Analyzing tweet %s" % k)
                tweets[k]['nlu'] = watson.call_nlu(tweet_text)
            except watson_developer_cloud.watson_developer_cloud_service.WatsonException:
                print("WatsonExcepption on %s" % k)
                tweets[k]['nlu'] = None
                pass
            except KeyError: 
                print("KeyError on tweet %s" % k)
                tweets[k]['nlu'] = None
                pass

    outfile = "watson_results_" + time.strftime("%Y-%m-%d_%H.%M.%S") + ".json"
    with open(outfile, "w+") as f:
       output = json.dumps(tweets, indent=4)
       f.write(output)

if __name__ == '__main__':
    main()