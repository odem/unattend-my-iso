import os
from os.path import isdir, isfile
import shutil
import subprocess
import requests
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.core.files.file_mounts import UmiFileMounts
from unattend_my_iso.common.logging import log_debug, log_error
from unattend_my_iso.core.files.file_replacements import UmiFileReplacements


class UmiFileManager(UmiFileMounts, UmiFileReplacements):

    def __init__(self):
        UmiFileReplacements.__init__(self)
        UmiFileMounts.__init__(self)

    def cwd(self):
        return os.getcwd()

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

    def http_download(self, url: str, name: str, dir: str) -> bool:
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

    def chmod(self, dst: str, privilege: int) -> bool:
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

    def _get_path_isovirtio(self, args: TaskConfig, template: TemplateConfig) -> str:
        isopath = args.sys.iso_path
        isoname = template.virtio_name
        return f"{isopath}/{isoname}"

    def _get_path_isosource(self, args: TaskConfig, template: TemplateConfig) -> str:
        isopath = args.sys.iso_path
        isoname = template.iso_name
        return f"{isopath}/{isoname}"

    def _get_path_isopath(self, args: TaskConfig) -> str:
        isopath = args.sys.iso_path
        isoname = args.target.template
        isoprefix = args.target.file_prefix
        return f"{isopath}/{isoprefix}{isoname}"

    def _get_path_isofile(self, args: TaskConfig) -> str:
        isopath = self._get_path_isopath(args)
        return f"{isopath}.{args.target.file_extension}"

    def _get_path_intermediate(self, args: TaskConfig) -> str:
        interpath = args.sys.intermediate_path
        intername = args.target.template
        return f"{interpath}/{intername}"

    def _get_path_template(self, args: TaskConfig) -> str:
        templatepath = args.sys.template_path
        templatename = args.target.template
        return f"{templatepath}/{templatename}"

    def _get_path_mountfile(self, args: TaskConfig, template: TemplateConfig) -> str:
        isopath = args.sys.iso_path
        isoname = template.iso_name
        return f"{isopath}/{isoname}"

    def _get_path_mountvirtio(self, args: TaskConfig, template: TemplateConfig) -> str:
        isopath = args.sys.mnt_path
        isoname = template.virtio_name
        return f"{isopath}/{isoname}"

    def _get_path_mountpath(self, args: TaskConfig) -> str:
        mntpath = args.sys.mnt_path
        targetname = args.target.template
        return f"{mntpath}/{targetname}"

    def _get_path_vm(self, args: TaskConfig):
        return f"{args.sys.vm_path}/{args.target.template}"
        return True
