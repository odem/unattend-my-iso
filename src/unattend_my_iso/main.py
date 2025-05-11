import logging
import sys
from unattend_my_iso.common.const import (
    DEBUG_OVERLAY,
    DEBUG_PROCTYPE,
    DEBUG_TEMPLATE,
    DEBUG_VERBOSITY,
)
from unattend_my_iso.core.reader.reader_cli import CommandlineReader
from unattend_my_iso.common.logging import init_logger, log_info
from unattend_my_iso.core.processing.processor import UmiTaskProcessor


def do_main(work_path: str = ""):
    proc = UmiTaskProcessor(work_path)
    proc.do_process()
    return None


def do_init(debug: bool):
    if debug:
        do_debug_init()
    reader = CommandlineReader()
    p = reader._create_cli_parser_all()
    args = p.parse_args()
    kwargs = args._get_kwargs()
    level = 3
    for item in kwargs:
        if item[0] == "verbosity":
            level = item[1] if item[1] is not None else 0
            break
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


def do_debug_init():
    sys.argv += ["-tt", DEBUG_TEMPLATE]
    sys.argv += ["-to", DEBUG_OVERLAY]
    sys.argv += ["-tp", DEBUG_PROCTYPE]
    sys.argv += ["-rv", DEBUG_VERBOSITY]


def main(work_path: str = "", debug: bool = False):
    do_init(debug)
    do_main(work_path)


if __name__ == "__main__":
    main()
