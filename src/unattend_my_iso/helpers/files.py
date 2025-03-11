import os
import subprocess
import shutil

from unattend_my_iso.helpers.logging import log_error, log_debug


def _get_copy_cmd(src: str, dst: str) -> list[str]:
    command = ["cp", "-r"]
    command += [f"{src}", dst]
    return command


def _get_chown_cmd(dst: str, user: str) -> list[str]:
    command = ["sudo", "chown", f"{user}:{user}", "-R"]
    command += [dst]
    return command


def _get_chmod_cmd(dst: str) -> list[str]:
    command = ["sudo", "chmod", "u+rw", "-R"]
    command += [dst]
    return command


def copy_file(src: str, dst: str) -> bool:
    shutil.copy(src, dst)
    return True


def copy_folder(src: str, dst: str) -> bool:
    try:
        # log_debug(f"Copy folder from '{src}' to '{dst}'")
        if os.path.exists(dst) is False:
            os.makedirs(dst)
        if os.path.exists(dst):
            command = _get_copy_cmd(src, dst)
            chown = _get_chown_cmd(dst, "jb")
            chmod = _get_chmod_cmd(dst)
            completed_proc = subprocess.run(command, capture_output=True, text=True)
            if completed_proc.returncode == 0:
                completed_chown = subprocess.run(chown, capture_output=True, text=True)
                if completed_chown.returncode == 0:
                    completed_chmod = subprocess.run(
                        chmod, capture_output=True, text=True
                    )
                    if completed_chmod.returncode == 0:
                        return True
            else:
                msg = (
                    f"Extract error {completed_proc.returncode}!\n"
                    f"{completed_proc.stdout.strip()}"
                    f"{completed_proc.stderr.strip()}"
                )
                log_error(msg)
        return True
    except Exception as exe:
        log_error(f"Error during extract operation: {exe}")
    return False
