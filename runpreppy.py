#! /usr/bin/env python
from preppy import Preppy, ReportWriter
from preppy import cd
import argparse


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-terms", "--terms", "-term", "--term",
                        nargs="+", help="Terms to search for",
                        default=['Truvada', '#PrEP'])
    parser.add_argument("-wd", "--wd",
                        help="Working directory path",
                        default="/Users/danielsnyder/devl/preppy/")
    return parser.parse_args()

args = _parse_args()


terms = args.terms
wd = args.wd

with cd(wd):
    Session = Preppy(
        session_file_path="preppy_session.json",
        config_file='config.json',
        backup_dir='backups'
    )
    Session.get_more_tweets(terms)
    reportwriter = ReportWriter(Session.tweets)
    reportwriter.write_report_geo("geo_tweet_report.csv")
    print(reportwriter.country_counts())
    Session.cleanup_session()
