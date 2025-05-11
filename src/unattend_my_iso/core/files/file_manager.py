import os
import shutil
import requests
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error
from unattend_my_iso.core.subprocess.caller import run
from unattend_my_iso.core.files.file_contents import UmiFileContents
from unattend_my_iso.core.files.file_mounts import UmiFileMounts
from unattend_my_iso.core.files.file_replacements import UmiFileReplacements


class UmiFileManager(UmiFileMounts, UmiFileContents, UmiFileReplacements):

    def __init__(self):
        UmiFileContents.__init__(self)
        UmiFileReplacements.__init__(self)
        UmiFileMounts.__init__(self)

    def cwd(self):
        return os.getcwd()

    def rm(self, src: str) -> bool:
        try:
            if os.path.exists(src):
                if os.path.isfile(src):
                    os.remove(src)
                elif os.path.isdir(src):
                    shutil.rmtree(src)
                else:
                    log_error("Cant delete unknown file object")
        except Exception as exe:
            log_error(f"Error on copy_file: {exe}")
            return False
        return True

    def mv(self, src: str, dst: str) -> bool:
        try:
            log_debug(f"Moving {src} to {dst}")
            if os.path.exists(src):
                shutil.move(src, dst)
        except Exception as exe:
            log_error(f"Error on copy_file: {exe}")
            return False
        return True

    def cp(self, src: str, dst: str) -> bool:
        try:
            if os.path.exists(src):
                if os.path.isfile(src):
                    shutil.copy(src, dst)
                elif os.path.isdir(src):
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
            run(["cp", "-r", src, dst])
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
        isopath = args.sys.path_iso
        isoname = template.virtio_name
        return f"{isopath}/{isoname}"

    def _get_path_isosource(self, args: TaskConfig, template: TemplateConfig) -> str:
        isopath = args.sys.path_iso
        isoname = template.iso_name
        return f"{isopath}/{isoname}"

    def _get_path_isopath(self, args: TaskConfig) -> str:
        isopath = args.sys.path_iso
        isoname = args.target.template
        isoprefix = args.target.file_prefix
        overlay = ""
        if args.target.template_overlay != "":
            overlay = args.target.template_overlay
            return f"{isopath}/{isoprefix}{isoname}.{overlay}"
        return f"{isopath}/{isoprefix}{isoname}"

    def _get_path_isofile(self, args: TaskConfig) -> str:
        isopath = self._get_path_isopath(args)
        return f"{isopath}.{args.target.file_extension}"

    def _get_path_intermediate(self, args: TaskConfig) -> str:
        interpath = args.sys.path_intermediate
        intername = args.target.template
        if args.target.template_overlay != "":
            return f"{interpath}/{intername}.{args.target.template_overlay}"
        return f"{interpath}/{intername}"

    def _get_path_template(self, args: TaskConfig) -> str:
        templatepath = args.sys.path_templates
        templatename = args.target.template
        return f"{templatepath}/iso/{templatename}"

    def _get_path_template_addon(self, name: str, args: TaskConfig) -> str:
        templatepath = args.sys.path_templates
        return f"{templatepath}/addons/{name}"

    def _get_path_addon_grub_theme(self, args: TaskConfig) -> str:
        srctmpl = self._get_path_template_addon("grub", args)
        return f"{srctmpl}/themes/{args.addons.grub.grub_theme}"

    def _get_path_mountfile(self, args: TaskConfig, template: TemplateConfig) -> str:
        isopath = args.sys.path_iso
        isoname = template.iso_name
        return f"{isopath}/{isoname}"

    def _get_path_mountvirtio(self, args: TaskConfig, template: TemplateConfig) -> str:
        isopath = args.sys.path_mnt
        isoname = template.virtio_name
        return f"{isopath}/{isoname}"

    def _get_path_mountpath(self, args: TaskConfig) -> str:
        mntpath = args.sys.path_mnt
        targetname = args.target.template
        return f"{mntpath}/{targetname}"

    def _get_path_vm(self, args: TaskConfig):
        return f"{args.sys.path_vm}/{args.run.vmname}"

    def _get_path_vmpid(self, args: TaskConfig):
        return f"{args.sys.path_vm}/{args.run.vmname}/{args.run.file_pid}"
