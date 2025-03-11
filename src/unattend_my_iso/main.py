import sys
from unattend_my_iso.process.processor import TaskProcessor


def do_main(script_name: str = "", arguments: list = [], work_path: str = ""):
    proc = TaskProcessor(work_path)
    proc.do_process(script_name, arguments)


def main(script_name: str = "", arguments: list = [], work_path: str = ""):
    do_main(script_name, arguments, work_path)


if __name__ == "__main__":
    script_name = sys.argv[0]
    arguments = sys.argv[1:]
    main(script_name, arguments)
