import logging
import sys
from unattend_my_iso.core.reader.cli_reader import CommandlineReader
from unattend_my_iso.common.logging import init_logger, log_debug, log_error, log_info
from unattend_my_iso.core.processing.processor import UmiTaskProcessor


def do_main(work_path: str = ""):
    proc = UmiTaskProcessor(work_path)
    proc.do_process()


def do_init(debug: bool):
    if debug:
        do_debug_init()
    reader = CommandlineReader()
    p = reader._create_cli_parser_all()
    args = p.parse_args()
    kwargs = args._get_kwargs()
    level = 0
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


def do_debug_init():
    sys.argv += ["-tt", "mps"]
    sys.argv += ["-to", "*"]
    sys.argv += ["-rv", "3"]
    print(f"ARGV: {sys.argv}")
    reader = CommandlineReader()
    p = reader._create_cli_parser_all()
    args = p.parse_args()
    kwargs = args._get_kwargs()
    for item in kwargs:
        log_error(f"ITEM: {item}", "INIT")


def main(work_path: str = "", debug: bool = False):
    do_init(debug)
    do_main(work_path)


if __name__ == "__main__":
    main()
