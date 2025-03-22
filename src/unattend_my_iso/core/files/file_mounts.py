import os
import subprocess
from unattend_my_iso.common.logging import log_error


class UmiFileMounts:

    def __init__(self):
        pass

    def _get_mount_cmd(
        self, src: str, dst: str, opts: str = "", fstype: str = ""
    ) -> list[str]:
        command = ["sudo", "mount"]
        if opts != "":
            command += ["-o", opts]
        if fstype != "":
            command += ["-t", fstype]
        command += [src, dst]
        return command

    def _get_unmount_cmd(self, dst: str) -> list[str]:
        command = ["sudo", "umount", dst]
        return command

    def mount_folder(
        self, src: str, dst: str, opts: str = "", fstype: str = ""
    ) -> bool:
        if os.path.exists(dst) is False:
            os.makedirs(dst)

        if os.path.exists(dst):
            command = self._get_mount_cmd(src, dst, opts, fstype)
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

    def unmount_folder(self, dir: str) -> bool:
        # log_debug(f"Unmount iso at '{dir}'")
        if os.path.exists(dir):
            command = self._get_unmount_cmd(dir)
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
