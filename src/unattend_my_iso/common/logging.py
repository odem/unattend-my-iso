import logging

LOGGER = None


def init_logger(level: int):
    global LOGGER
    logging.basicConfig(level=level)
    LOGGER = logging.getLogger()


def log_message(msg: str, level: int):
    global LOGGER
    if LOGGER is not None:
        LOGGER.log(msg=msg, level=level)
    else:
        print(f"No Logger: {msg}")


def log_debug(msg: str):
    log_message(msg=msg, level=logging.DEBUG)


def log_info(msg: str):
    log_message(msg=msg, level=logging.INFO)


def log_warn(msg: str):
    log_message(msg=msg, level=logging.WARN)


def log_error(msg: str):
    log_message(msg=msg, level=logging.ERROR)
