#!/usr/bin/env python
from preppy import (
    Preppy, cd
)
from preppy.report_writer import ReportWriter
import argparse
import logging
import subprocess


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-terms", "--terms", "-term", "--term",
                        nargs="+", help="Terms to search for",
                        default=[])
    parser.add_argument("-wd", "--wd",
                        help="Working directory path",
                        default=".")
    parser.add_argument("-encode", "--encode",
                        help="The name of the variable to encode",
                        default="", type=str)
    parser.add_argument("-report", "--report",
                        help="If provided, reports will be written",
                        action="store_true",
                        default=False)
    parser.add_argument("-ntweets", "--ntweets", "-ntweet", "--ntweet",
                        help="How many tweets? can be used for -encode",
                        default=0, type=int)
    parser.add_argument("-updatetweets",
                        action="store_true",
                        default=False)
    parser.add_argument("-debug", "--debug",
                        action="store_true",
                        help="If true, send debug messages to log file",
                        default=False)
    parser.add_argument("-noclean", "--noclean", "-nocleanup", "--nocleanup",
                        help="If present, preppy session will not be saved and no backups will be made",
                        action="store_true",
                        default=False)
    parser.add_argument("-keyword_classify", "--keyword_classify", "-keyword", "--keyword",
                        help="Preppy will write a csv report, run keyword_classify.R, and store the results",
                        action="store_true",
                        default=False)
    parser.add_argument("-watson", "--watson",
                        help="Send tweets through watson",
                        action="store_true",
                        default=False)
    parser.add_argument("-nwatson", "--nwatson",
                        help="Number of tweets to send to Waston (default=200)",
                        default=200, type=int)
    return parser.parse_args()


args = _parse_args()
terms = args.terms
wd = args.wd
encode = args.encode
debug = args.debug
report = args.report
ntweets = args.ntweets
updatetweets = args.updatetweets
noclean = args.noclean
keyword_classify = args.keyword_classify
watson = args.watson
n_watson = args.nwatson

# Configure logging here
logger = logging.getLogger('preppy')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("preppy.log")
fh.setLevel(logging.DEBUG)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
fm = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(fm)
sh.setFormatter(fm)
logger.addHandler(fh)
logger.addHandler(sh)

with cd(wd):
    logger.info("Starting Preppy Session")
    session_file = "preppy_session.json"

    Session = Preppy(
        session_file_path=session_file,
        config_file='config.json',
        backup_dir='backups'
    )

    logger.info("Opened {:} session file"
                .format(session_file))
    if updatetweets:
        logger.info("Updating old tweets")
        Session.status_prior()
        Session.rehydrate_tweets()
        Session.status_posterior()
    if terms:
        logger.info("Retrieving new tweets")
        Session.get_more_tweets(terms)
    if keyword_classify:
        reportwriter = ReportWriter(Session)
        reportwriter.write_report_geo("geo_tweet_report.xls", fmt='xls')
        subprocess.call(["Rscript", "./scripts/keyword_classify.R", "geo_tweet_report.xls"])
        Session.encode_rscript_results()

    if encode:
        if encode == "user_place":
            Session.encode_user_location(nmax=ntweets)
        else:
            Session.encode_variable(
                variable_name=encode,
                max_tweets=ntweets,
                only_geo=True
            )
            Session.tweets.tweets_coding_status()

    if watson:
        Session.get_nlu_data(sample_size=n_watson, randomize=True)
        report_writer = ReportWriter(Session)
        report_writer.write_report_nlu("watson_report.csv")

    if report:
        Session.tweets.export_geotagged_tweets("geotagged_tweets.json")
        reportwriter = ReportWriter(Session)
        reportwriter.write_report_all("all_tweets_report.xlsx", fmt='excel')
        reportwriter.write_report_geo("geo_tweet_report.xlsx", fmt='excel')
        reportwriter.hashtag_table("hashtag_frequencies.json", min_freq=10)
        logger.info("There are {:} geotagged tweets".format(reportwriter.how_many_geotagged()))
        logger.info(reportwriter.country_counts())
        logger.info(reportwriter.state_counts())
        unique_states = reportwriter.unique_states()
        logger.info("There are {:} unique states".format(unique_states.__len__()))
    if not noclean:
        Session.cleanup_session()
