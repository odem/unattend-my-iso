import os
import tomllib
from typing import Any, Optional
from unattend_my_iso.common.logging import log_error


class TomlReader:
    def __init__(self) -> None:
        pass

    def read_toml_file(self, file: str) -> Optional[dict[str, Any]]:
        if os.path.exists(file):
            try:
                with open(file, "rb") as f:
                    return tomllib.load(f)
            except Exception as exe:
                log_error(f"Exception on toml read: {exe}")
        else:
            log_error("Template config is not a valid file")
        return None
