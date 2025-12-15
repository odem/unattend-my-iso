import os
from unattend_my_iso.common.logging import log_error


class UmiFileContents:

    def __init__(self):
        pass

    def makedirs(self, dirname: str) -> str:
        try:
            if os.path.exists(dirname) is False:
                os.makedirs(dirname)
        except Exception as e:
            log_error(f"Exception on file append: {e}")
        return ""

    def read_file(self, filename: str) -> str:
        try:
            with open(filename, "r") as file:
                return file.read()
        except Exception as e:
            log_error(f"Exception on file append: {e}")
        return ""

    def append_to_file(self, filename: str, text_to_append: str) -> bool:
        try:
            with open(filename, "a") as file:
                file.write(text_to_append)
                return True
        except Exception as e:
            log_error(f"Exception on file append: {e}")
        return False

    def touch_file(self, filename: str) -> bool:
        try:
            with open(filename, "w") as file:
                file.write("")
                return True
        except Exception as e:
            log_error(f"Exception on file touch: {e}")
        return False
