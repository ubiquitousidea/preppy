# preppy
Application used for academic research into public discussion of HIV and PrEP

## Basic Operating Info
The main driver script runpreppy.py requires the presence of a config file (config.json) and a code book file (codebook.json). The config file should contain the twitter authentication credentials needed for the API queries. They are a dictionary of the four arguments needed to instantiate a twitter.API object (from python-twitter package):
{"consumer_key": "...", "consumer_secret": "...", "access_token_key", "...", "access_token_secret": "..."}. These can be obtained from the twitter developer page and going to "My Apps".

## Run Preppy
Calling "runpreppy.py -terms X Y Z" will sequentially search for terms X Y and Z using the twitter search api. It will continue searching, retrieving most recent tweets until finding a tweet that it has already found. Searching is terminated when the ID of a returned tweet is less than the maximum ID currently stored.
The last session of tweets is loaded from local cache "preppy_session.json". The session files are backup up into a subdir "backups" and the 50 most recent files are kept.

## Encoding Parameters (such as Relevance)
Call "runpreppy.py -encode X -encode N" to start coding N tweets. X is which ever parameter name you want to be asked about. The script will show the tweet and a list of its hashtags. User will be prompted to input a numerical value (and 30 times again or until the input is valid). Invalid inputs will make the script print the dictionary of valid inputs and their meanings.
codebook.json contains the parameter names, valid values, and definitions of what each value means.

## Producing Reports
Call "runpreppy.py -report" or add "-report" to any other call and it will be parsed by argparse.
The main report call will produce a table of tweets in csv format. Columns include tweet ID, date, text, user id, {longitude, latitude, city, state, country} (if available).
It will also produce (for a development feature) a json file of tweet hashtags and their frequencies in relevant and irrelevant tweets of the form:
{"hashtag": {"RELEVANT": I, "IRRELEVANT": J, "UNKNOWN": K},...} where I, J, and K are the number of times those tweets were found in tweets that were coded as relevant, irrelevant, or uncoded. The hope was that eventually I would have time to use this information to try to select factors for a support vector machine classifier (or other classifying model).

## Other Script Arguments Available.
Other args include:
- "wd": change the working directory where the "preppy_session.json" session file will be stored.
- "updatetweets": If in the event of code development you destroy the contents of your tweet dictionary inside preppy_session.json, run this command "runpreppy.py -updatetweets" and a custom API call will be used to retrieve the tweet contents for each of the tweet ID's stored in batches of 100 (be aware of the rate limit of 180 calls per 15 minute block).
(Consider forking bear/python-twitter, writing this into the twitter.API class, and pull requesting). You should probably ask first. I'm not sure how people feel about random pull requests from strangers.
- "debug": Some extra printed info. Not really hooked up to much right now.
- "noclean": suppress the save and backup operations (session writes no session file and performs no backup of the latest session file).