import logging
import sys
from unattend_my_iso.core.reader.reader_cli import CommandlineReader
from unattend_my_iso.common.logging import init_logger, log_info
from unattend_my_iso.core.processing.processor import UmiTaskProcessor
from unattend_my_iso.common.const import (
    DEBUG_OVERLAY,
    DEBUG_PROCTYPE,
    DEBUG_TEMPLATE,
    DEBUG_VERBOSITY,
    DEBUG_WORKDIR,
    DEFAULT_DEBUG_LEVEL,
)


def do_main():
    proc = UmiTaskProcessor()
    proc.do_process()
    return None


def do_init(debug: bool):
    reader = CommandlineReader()
    p = reader._create_cli_parser_all()
    args = p.parse_args()
    kwargs = args._get_kwargs()
    level = 3
    for item in kwargs:
        if item[0] == "template":
            debug = True
        if item[0] == "verbosity":
            level = item[1] if item[1] is not None else DEFAULT_DEBUG_LEVEL
    if level == 0:
        init_logger(logging.ERROR)
    elif level == 1:
        init_logger(logging.WARN)
    elif level == 2:
        init_logger(logging.INFO)
    elif level == 3:
        init_logger(logging.DEBUG)
    elif level > 3:
        init_logger(logging.DEBUG)
    if debug:
        do_debug_init()


def do_debug_init():
    log_info("No params detected. Using default values for debugging", "Configreader")
    sys.argv += ["-tt", DEBUG_TEMPLATE]
    sys.argv += ["-to", DEBUG_OVERLAY]
    sys.argv += ["-tp", DEBUG_PROCTYPE]
    sys.argv += ["-rv", DEBUG_VERBOSITY]
    sys.argv += ["-tw", DEBUG_WORKDIR]


def main(debug: bool = False):
    do_init(debug)
    do_main()


if __name__ == "__main__":
    main()
