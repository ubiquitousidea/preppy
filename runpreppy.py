#! /usr/bin/env python
from bin.prep import Preppy, ReportWriter


termlist = ["Truvada", "#PrEP"]
Session = Preppy(
    session_file_path="preppy_session.json",
    config_file='config.json',
    backup_dir='./backups'
)
Session.get_more_tweets(termlist)
reportwriter = ReportWriter(Session.tweets)
reportwriter.write_report_geo("geo_tweet_report.csv")
report = reportwriter.table_all
print(report.country.value_counts())
Session.cleanup_session()
