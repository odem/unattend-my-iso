import logging
from unattend_my_iso.core.reader.cli_reader import CommandlineReader
from unattend_my_iso.common.logging import init_logger
from unattend_my_iso.core.processing.processor import TaskProcessor


def do_main(work_path: str = ""):
    proc = TaskProcessor(work_path)
    proc.do_process()


def do_init():
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


def main(work_path: str = ""):
    do_init()
    do_main(work_path)


if __name__ == "__main__":
    main()
