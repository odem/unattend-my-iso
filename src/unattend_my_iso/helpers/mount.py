import os
import subprocess
from unattend_my_iso.helpers.logging import log_error


def _get_mount_cmd(src: str, dst: str, fstype: str = "") -> list[str]:
    command = ["sudo", "mount"]
    if fstype != "":
        command += ["-t", fstype]
    command += [src, dst]
    return command


def _get_unmount_cmd(dst: str) -> list[str]:
    command = ["sudo", "umount", dst]
    return command


def mount_folder(src: str, name: str, dst: str) -> bool:
    full = f"{dst}/{name}"
    if os.path.exists(full) is False:
        os.makedirs(full)
    if os.path.exists(full):
        command = _get_mount_cmd(src, full)
        completed_proc = subprocess.run(command, capture_output=True, text=True)
        if completed_proc.returncode == 0:
            return True
        else:
            msg = (
                f"Mount error {completed_proc.returncode}!\n"
                f"{completed_proc.stdout.strip()}"
                f"{completed_proc.stderr.strip()}"
            )
            log_error(msg)
    return False


def unmount_folder(dir: str) -> bool:
    # log_debug(f"Unmount iso at '{dir}'")
    if os.path.exists(dir):
        command = _get_unmount_cmd(dir)
        completed_proc = subprocess.run(command, capture_output=True, text=True)
        if completed_proc.returncode == 0:
            os.rmdir(dir)
            return True
        else:
            msg = (
                f"Unmount error {completed_proc.returncode}!\n"
                f"{completed_proc.stdout.strip()}"
                f"{completed_proc.stderr.strip()}"
            )
            log_error(msg)
    return False
