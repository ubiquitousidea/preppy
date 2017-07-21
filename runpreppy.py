#! /usr/bin/env python
from bin.prep import Preppy


termlist = ["Truvada", "#PrEP"]
Session = Preppy(
    session_file_name="bin/preppy_session.json",
    config_file='bin/config.json')
Session.get_more_tweets(termlist)
Session.tweets.export_geotagged_tweets()
Session.cleanup_session()
