import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def log_debug(msg: str):
    logger.log(msg=msg, level=logging.DEBUG)


def log_info(msg: str):
    logger.log(msg=msg, level=logging.INFO)


def log_warn(msg: str):
    logger.log(msg=msg, level=logging.WARN)


def log_error(msg: str):
    logger.log(msg=msg, level=logging.ERROR)
