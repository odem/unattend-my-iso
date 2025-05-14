import os
from unattend_my_iso.common.logging import log_debug, log_error


class UmiFileReplacements:

    def __init__(self):
        pass

    def replace_string(self, file_path: str, find: str, replace: str | bool) -> bool:
        try:
            with open(file_path, "r") as file:
                content = file.read()
            if isinstance(replace, bool):
                term = "true" if replace else "false"
            else:
                term = replace
            updated_content = content.replace(find, term)
            with open(file_path, "w") as file:
                file.write(updated_content)
            basename = os.path.basename(file_path)

            # withpart = f" with '{replace}'"
            withpart = ""
            log_debug(
                f"Replaced '{find}'{withpart} in {basename}",
                self.__class__.__qualname__,
            )
            return True
        except Exception as e:
            log_error(
                f"An error occurred during file replacemnt: {file_path} -> {e}",
                self.__class__.__qualname__,
            )
        return False
