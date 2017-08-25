#! /usr/bin/env python
from preppy import (
    Preppy, cd
)
from preppy.report_writer import ReportWriter
import argparse
import logging
import sys


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-terms", "--terms", "-term", "--term",
                        nargs="+", help="Terms to search for",
                        default=[])
    parser.add_argument("-wd", "--wd",
                        help="Working directory path",
                        default="/Users/danielsnyder/devl/preppy/")
    parser.add_argument("-encode", "--encode",
                        help="The name of the variable to encode",
                        default="", type=str)
    parser.add_argument("-report", "--report",
                        help="If provided, reports will be written",
                        action="store_true",
                        default=False)
    parser.add_argument("-ntweets", "--ntweets",
                        help="How many tweets? can be used for -encode",
                        default=0, type=int)
    parser.add_argument("-updatetweets",
                        action="store_true",
                        default=False)
    parser.add_argument("-debug", "--debug",
                        action="store_true",
                        help="If true, send debug messages to log file",
                        default=False)
    return parser.parse_args()


args = _parse_args()
terms = args.terms
wd = args.wd
encode = args.encode
debug = args.debug
report = args.report
ntweets = args.ntweets
updatetweets = args.updatetweets


with cd(wd):
    logging.info("Starting Preppy Session")
    session_file = "preppy_session.json"

    Session = Preppy(
        session_file_path=session_file,
        config_file='config.json',
        backup_dir='backups'
    )

    logging.info("Opened {:} session file"
                 .format(session_file))
    if updatetweets:
        print("Updating old tweets")
        Session.status_prior()
        Session.rehydrate_tweets()
        Session.status_posterior()
        Session.cleanup_session()
    if terms:
        logging.info("Retrieving new tweets")
        Session.get_more_tweets(terms)
    if encode:
        Session.encode_variable(
            variable_name=encode,
            max_tweets=ntweets,
            only_geo=True
        )
        Session.tweets.tweets_coding_status()
    if report:
        Session.tweets.export_geotagged_tweets("geotagged_tweets.json")
        reportwriter = ReportWriter(Session)
        reportwriter.write_report_geo("geo_tweet_report.csv")
        print(reportwriter.country_counts())
        print(reportwriter.state_counts())
        unique_states = reportwriter.unique_states()
        logging.info("There are {:} unique states".format(unique_states.__len__()))
    Session.cleanup_session()
