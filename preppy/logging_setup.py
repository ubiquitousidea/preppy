import logging


def start_logging(file_name=None, debug=False):
    """
    A function that sets up the log path and the logging level
        ("debug", "info", "warning", "critical")
    :param file_name: Optional file name to write the logging statements to
    :param debug:
        If true, debug statements will appear.
        If False, level is set to INFO
    :return:
    """
    if file_name is None:
        file_name = "logfile.txt"
    logging.basicConfig(filename=file_name)
    stderrLogger = logging.StreamHandler()
    stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    logging.getLogger().addHandler(stderrLogger)
    # level = logging.DEBUG if debug is True else logging.INFO
    # logging_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # args = dict(level=level, format=logging_fmt)
    # if file_name:
    #     args.update(
    #         dict(filename=file_name)
    #     )
    # else:
    #     args.update(
    #         dict(
    #             stream=sys.stdout
    #         )
    #     )
    # logging.basicConfig(**args)

