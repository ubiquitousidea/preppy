import logging
import sys


def start_streaming_log(debug=False):
    """
    Answer from Martijn Pieters
    https://stackoverflow.com/questions/14058453/making-python-loggers-output-all-messages-to-stdout-in-addition-to-log
    :param debug: If true, write the debug messages. Else use logging level: INFO
    :return:
    """
    level = logging.DEBUG if debug is True else logging.INFO
    root = logging.getLogger()
    root.setLevel(level)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)


def start_logging_to_file(file_name, debug=False):
    """
    A function that sets up the log path and the logging level
        ("debug", "info", "warning", "critical")
    :param file_name:
    :param debug:
    :return:
    """
    level = logging.DEBUG if debug is True else logging.INFO
    loggin_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename=file_name,
                        level=level,
                        format=loggin_fmt)
