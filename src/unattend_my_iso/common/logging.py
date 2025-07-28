import logging
from unattend_my_iso.common.const import LOGGER


def init_logger(level: int):
    global LOGGER
    logging.basicConfig(
        level=level,
        format="[%(levelname)7s]%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    LOGGER = logging.getLogger()


def log_message(msg: str, topic: str, level: int):
    global LOGGER
    if LOGGER is not None:
        fullmsg = f"[{topic:18}] {msg}"
        LOGGER.log(msg=fullmsg, level=level)
    else:
        print(f"No Logger: {msg}")


def log_debug(msg: str, topic: str = ""):
    log_message(msg=msg, topic=topic, level=logging.DEBUG)


def log_info(msg: str, topic: str = ""):
    log_message(msg=msg, topic=topic, level=logging.INFO)


def log_warn(msg: str, topic: str = ""):
    log_message(msg=msg, topic=topic, level=logging.WARN)


def log_error(msg: str, topic: str = ""):
    log_message(msg=msg, topic=topic, level=logging.ERROR)
