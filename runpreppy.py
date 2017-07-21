#! /usr/bin/env python
from bin.prep import Preppy


termlist = ["Truvada", "#PrEP"]
Session = Preppy(
    session_file_path="preppy_session.json",
    config_file='config.json',
    backup_dir='./backups'
)
Session.get_more_tweets(termlist)
Session.tweets.export_geotagged_tweets()
Session.cleanup_session()
