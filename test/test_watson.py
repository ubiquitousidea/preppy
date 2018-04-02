from preppy import (
    Preppy, cd
)
from preppy.report_writer import ReportWriter

with cd('~/preppy/'):
    print("Starting Preppy Session")
    session_file = "preppy_session.json"

    Session = Preppy(
        session_file_path=session_file,
        config_file='config.json',
        backup_dir='backups'
    )

    Session.get_nlu_data(sample_size=200, randomize=True)

    report_writer = ReportWriter(Session)
    report_writer.write_report_nlu(".")