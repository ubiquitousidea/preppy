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

parser = argparse.ArgumentParser()
parser.add_argument("infile")
args = parser.parse_args()
infile = args.infile
config_file = args.config_file

def get_waston_nlu(config_file):
    """Instantiates watson NLU api object with keys from config.json"""
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
            watson_info = config.get("watson")
            username = watson_info.get('username')
            password = watson_info.get('password')
            version = watson_info.get('version')
            nlu = watson_developer_cloud.NaturalLanguageUnderstandingV1(
                username=username,
                password=password
                version=version)
        return nlu
    except:
        print("Unable to connect to Watson API\nCheck config.json")
        quit()

def nlu_analyze(txt):
    """Makes call to Watson NLU API"""
    result = nlu.analyze(
        text=txt,
        features = [features.Concepts(), features.Keywords(), features.Emotion(), features.Sentiment()]
        )
    return result 

def main():
    with open(infile) as f:
        tweets = json.load(f)

        nlu = get_waston_nlu()

        for k in tweets.keys():
            try:
                tweet_text = tweets[k]['full_text']
                print("Analyzing tweet %s" % k)
                tweets[k]['nlu'] = nlu_analyze(tweet_text)
            except watson_developer_cloud.watson_developer_cloud_service.WatsonException:
                print("WatsonExcepption on %s" % k)
                tweets[k]['nlu'] = None
                pass
            except KeyError: 
                print("KeyError on tweet %s" % k)
                tweets[k]['nlu'] = None
                pass

        outfile = "watson_results_" + time.strftime("%Y-%m-%d_%H.%M.%S") + ".json"
    with open("outfile", "w") as f:
        f = json.dumps(tweets, f, indent=4)

if __name__ == '__main__':
    main()