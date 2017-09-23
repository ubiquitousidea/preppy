# preppy
Application used for academic research into public discussion of HIV and PrEP

## Basic Operating Info
The main driver script runpreppy.py requires the presence of a config file and a code book file. The config file should contain the twitter authentication credentials needed for the API queries. They are a dictionary of the four arguments needed to instantiate a twitter.API instance (from python-twitter package):
{"consumer_key": "...", "consumer_secret": "...", "access_token_key", "...", "access_token_secret": "..."}. These can be obtained from the twitter developer page and going to "My Apps".

## Code Book
The code book (codebook.json) is used when coding tweets after calling "runpreppy.py -encode X" where X is which ever parameter name you want to be asked about. The script will show the tweet and a list of its hashtags. User will be prompted to input a numerical value (and 30 times again or until the input is valid). Invalid inputs will make the script print the dictionary of valid inputs and their meanings.

## Run Preppy
Calling "runpreppy.py -terms X Y Z" will sequentially search for terms X Y and Z using the twitter search api. It will continue searching, retrieving most recent tweets until finding a tweet that it has already found. Searching is terminated when the ID of a returned tweet is less than the maximum ID currently stored.

## Producing Reports
Call "runpreppy.py -report" or add "-report" to any other call and it will be parsed by argparse.
The main report call will produce a table of tweets in csv format. Columns include tweet ID, date, text, user id, {longitude, latitude, city, state, country} (if available).
It will also produce (for a development feature) a json file of tweet hashtags and their frequencies in relevant and irrelevant tweets of the form:
{"hashtag": {"RELEVANT": I, "IRRELEVANT": J, "UNKNOWN": K},...} where I, J, and K are the number of times those tweets were found in tweets that were coded as relevant, irrelevant, or uncoded. The hope was that eventually I would have time to use this information to try to select factors for a support vector machine classifier (or other classifying model).
