#! /usr/bin/env python
from preppy import (
    Preppy, ReportWriter, cd
)
from preppy.logging_setup import start_logging_to_file
import argparse
import logging


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-terms", "--terms", "-term", "--term",
                        nargs="+", help="Terms to search for",
                        default=['Truvada', '#PrEP'])
    parser.add_argument("-wd", "--wd",
                        help="Working directory path",
                        default="/Users/danielsnyder/devl/preppy/")
    parser.add_argument("-encode", "--encode",
                        help="The name of the variable to encode",
                        default=None)
    parser.add_argument("-debug", "--debug",
                        action="store_true",
                        help="If true, send debug messages to log file",
                        default=False)
    return parser.parse_args()


args = _parse_args()
terms = args.terms
wd = args.wd
var_name = args.encode
debug = args.debug


with cd(wd):
    start_logging_to_file("preppy.log", debug=debug)
    logging.info("Starting Preppy Session -----------------------------------")
    session_file = "preppy_session.json"
    Session = Preppy(
        session_file_path=session_file,
        config_file='config.json',
        backup_dir='backups'
    )
    logging.info("Opened {:} session file"
                 .format(session_file))
    if var_name is None:
        logging.info("Retrieving new tweets")
        Session.get_more_tweets(terms)
        reportwriter = ReportWriter(Session)
        reportwriter.write_report_geo("geo_tweet_report.csv")
        print(reportwriter.country_counts())
        print(reportwriter.state_counts())
        unique_states = reportwriter.unique_states()
        logging.info("There are {:} unique states".format(unique_states.__len__()))
        Session.cleanup_session()
    else:
        Session.encode_variable(var_name.upper(), "test", max_tweets=20)
        Session.cleanup_session()
