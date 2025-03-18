import os
from os.path import isdir, isfile
import shutil
import subprocess
from unattend_my_iso.helpers.logging import log_error


class UmiFileManager:

    def __init__(self):
        pass

    def rm(self, src: str) -> bool:
        try:
            if os.path.exists(src):
                if isfile(src):
                    os.remove(src)
                elif isdir(src):
                    shutil.rmtree(src)
                else:
                    log_error("Cant delete unknown file object")
        except Exception as exe:
            log_error(f"Error on copy_file: {exe}")
            return False
        return True

    def mv(self, src: str, dst: str) -> bool:
        try:
            if os.path.exists(src):
                shutil.move(src, dst)
        except Exception as exe:
            log_error(f"Error on copy_file: {exe}")
            return False
        return True

    def cp(self, src: str, dst: str) -> bool:
        try:
            if os.path.exists(src):
                if isfile(src):
                    shutil.copy(src, dst)
                elif isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True, symlinks=True)
                else:
                    log_error("Cant delete unknown file object")
        except Exception as exe:
            log_error(f"Error on copy_file: {exe}")
            return False
        return True

    def copy_folder_iso(self, src: str, dst: str) -> bool:
        try:
            self.rm(dst)
            subprocess.run(["cp", "-r", src, dst])
        except Exception as exe:
            log_error(f"Error on copy_folder_iso: {exe}")
            return False
        return True

    def ensure_privilege(self, dst: str, privilege: int) -> bool:
        try:
            current_permissions = os.stat(dst).st_mode
            new_permissions = current_permissions | privilege
            os.chmod(dst, new_permissions)
            for root, dirs, files in os.walk(dst):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    current_permissions = os.stat(dir_path).st_mode
                    new_permissions = current_permissions | privilege
                    os.chmod(dir_path, new_permissions)
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    current_permissions = os.stat(file_path).st_mode
                    new_permissions = current_permissions | privilege
                    os.chmod(file_path, new_permissions)
        except Exception as exe:
            log_error(f"Error on ensure_privilege {privilege}: {exe}")
            return False
        return True
