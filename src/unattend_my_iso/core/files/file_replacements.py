import os
from unattend_my_iso.common.logging import log_debug, log_error


class UmiFileReplacements:

    def __init__(self):
        pass

    def replace_string(self, file_path: str, find: str, replace: str) -> bool:
        try:
            with open(file_path, "r") as file:
                content = file.read()
            updated_content = content.replace(find, replace)
            with open(file_path, "w") as file:
                file.write(updated_content)
            basename = os.path.basename(file_path)

            log_debug(f"File Replace : '{find}' with '{replace}' in {basename}")
            return True
        except Exception as e:
            log_error(f"An error occurred during file replacemnt: {file_path} -> {e}")
        return False
