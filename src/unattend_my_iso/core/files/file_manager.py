import os
import shutil

from unattend_my_iso.helpers.logging import log_error


class UmiFileManager:

    def __init__(self):
        pass

    def copy_file(self, src: str, dst: str) -> bool:
        try:
            shutil.copy(src, dst)
        except Exception as exe:
            log_error(f"Error on copy_file: {exe}")
            return False
        return True

    def copy_folder(self, src: str, dst: str) -> bool:
        try:
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst, dirs_exist_ok=True, symlinks=True)
        except Exception as exe:
            log_error(f"Error on copy_folder: {exe}")
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
