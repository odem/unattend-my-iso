from unattend_my_iso.process.processor import TaskProcessor


def do_main(work_path: str = ""):
    proc = TaskProcessor(work_path)
    proc.do_process()


def main(work_path: str = ""):
    do_main(work_path)


if __name__ == "__main__":
    main()
