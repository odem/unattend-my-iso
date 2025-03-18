import os
import requests
from unattend_my_iso.helpers.logging import log_error, log_debug


def download_file(url: str, name: str, dir: str) -> bool:
    try:
        os.makedirs(dir, exist_ok=True)
        log_debug(f"Requesting: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            dst = f"{dir}/{name}"
            log_debug(f"Download success! Storing to '{dst}'")
            if os.path.exists(dir):
                with open(dst, "wb") as file:
                    file.write(response.content)
                    return True
            else:
                log_error(f"Iso folder does not exist: '{dir}'")
        else:
            log_error(f"Download failed! Url: {url}")
    except Exception as exe:
        log_error(f"Download failed! Url: {url}\n{exe}")
    return False
