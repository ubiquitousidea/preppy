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
    parser.add_argument("-task", "--task",
                        help="Which task to execute; in (\'sentiment\', \'getnew\')",
                        default="getnew")
    return parser.parse_args()

args = _parse_args()


terms = args.terms
wd = args.wd
task = args.task

with cd(wd):
    Session = Preppy(
        session_file_path="preppy_session.json",
        config_file='config.json',
        backup_dir='backups'
    )
    if task == "getnew":
        Session.get_more_tweets(terms)
        reportwriter = ReportWriter(Session)
        reportwriter.write_report_geo("geo_tweet_report.csv")
        print(reportwriter.country_counts())
        print(reportwriter.state_counts())
        unique_states = reportwriter.unique_states()
        print("There are {:} unique states".format(unique_states.__len__()))
        Session.cleanup_session()
    elif task == "sentiment":
        Session.encode_sentiment("test", max_tweets=10)
        Session.cleanup_session()
