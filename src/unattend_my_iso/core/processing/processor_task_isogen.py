import os
from typing import Optional
from unattend_my_iso.common.common import TaskResult
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.core.processing.processor_base import TaskProcessorBase
from unattend_my_iso.common.logging import log_debug, log_error, log_info


class TaskProcessorIsogen(TaskProcessorBase):

    def __init__(self, work_path: str = ""):
        TaskProcessorBase.__init__(self, work_path)

    def task_build_all(self, args: TaskConfig, user: str) -> TaskResult:
        template = self._get_task_template(args)
        if template is None:
            return self._get_error_result("No template")
        if self._ensure_task_iso(args, template) is False:
            return self._get_error_result("No ISO")
        if self._extract_iso_contents(args, template) is False:
            return self._get_error_result("Not extracted")
        if self._copy_addons(args, template) is False:
            return self._get_error_result("Addons not copied")
        if self._prepare_bootloader(args, template) is False:
            return self._get_error_result("irmod not created")
        if self._generate_iso(args, template, user) is False:
            return self._get_error_result("iso not generated")
        return self._get_success_result()

    def task_build_intermediate(self, args: TaskConfig) -> TaskResult:
        template = self._get_task_template(args)
        if template is None:
            return self._get_error_result("No template")
        if self._ensure_task_iso(args, template) is False:
            return self._get_error_result("No ISO")
        if self._extract_iso_contents(args, template) is False:
            return self._get_error_result("Not extracted")
        return self._get_success_result()

    def task_build_addons(self, args: TaskConfig) -> TaskResult:
        template = self._get_task_template(args)
        if template is None:
            return self._get_error_result("No template")
        if self._copy_addons(args, template) is False:
            return self._get_error_result("Addons not copied")
        return self._get_success_result()

    def task_build_irmod(self, args: TaskConfig) -> TaskResult:
        template = self._get_task_template(args)
        if template is None:
            return self._get_error_result("No template")
        if self._prepare_bootloader(args, template) is False:
            return self._get_error_result("irmod not created")
        return self._get_success_result()

    def task_build_iso(self, args: TaskConfig, user: str) -> TaskResult:
        template = self._get_task_template(args)
        if template is None:
            return self._get_error_result("No template")
        if self._generate_iso(args, template, user) is False:
            return self._get_error_result("iso not generated")
        return self._get_success_result()

    def _generate_iso(
        self, args: TaskConfig, template: TemplateConfig, user: str
    ) -> bool:
        dst = self.files._get_path_isopath(args)
        fullinter = self.files._get_path_intermediate(args)
        created = self.isogen.create_iso(
            args, template, fullinter, template.name, dst, user, args.target.mbrfile
        )
        if created is True:
            log_info(f"Created ISO   : {dst}")
        return created

    def _prepare_bootloader(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if template.iso_type == "windows":
            return self._create_efidisk_windows(args)
        else:
            return self._create_irmod_linux(args)

    def _create_efidisk_windows(self, args: TaskConfig) -> bool:
        dstinter = self.files._get_path_intermediate(args)
        try:
            if self.isogen.create_efidisk_windows(args, dstinter) is False:
                log_error(f"Error creating efidisk for windows: {dstinter}")
                return False
        except Exception as exe:
            log_error(f"Exception: {exe}")
        return True

    def _create_irmod_linux(self, args: TaskConfig) -> bool:
        dstinter = self.files._get_path_intermediate(args)
        modpath = f"{dstinter}/irmod"
        initrdlist = self._extract_ramdisks(dstinter)
        try:
            for initrd in initrdlist:
                subdir = os.path.dirname(initrd)
                if subdir in args.addons.grub.initrd_list:
                    if self.isogen.create_irmod(subdir, modpath, dstinter) is False:
                        log_error(f"Error creating irmod: {subdir}")
                        return False
                else:
                    log_info(f"Skipped irmod : {initrd}")
        except Exception as exe:
            log_error(f"Exception: {exe}")
        return True

    def _extract_ramdisks(self, path: str) -> list[str]:
        matches = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.startswith("initrd") and file.endswith(".gz"):
                    filepath = os.path.join(root, file)
                    filepath = filepath.removeprefix(path)
                    if filepath.startswith("/"):
                        filepath = filepath.removeprefix("/")
                    log_debug(f"FILE: {filepath}")
                    matches.append(filepath)
        return matches

    def _copy_addons(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if args.addons.answerfile.enabled:
            self._copy_addon("answerfile", args, template)
        if args.addons.grub.enabled:
            self._copy_addon("grub", args, template)
        if args.addons.ssh.enabled:
            self._copy_addon("ssh", args, template)
        if args.addons.postinstall.enabled:
            self._copy_addon("postinstall", args, template)
        return True

    def _copy_addon(
        self, name: str, args: TaskConfig, template: TemplateConfig
    ) -> bool:
        addon = self.addons[name]
        success = addon.integrate_addon(args, template)
        log_info(f"Integrated    : {success}\t-> {addon.addon_name}")
        return success

    def _extract_iso_contents(self, args: TaskConfig, template: TemplateConfig) -> bool:
        dir_mount = self.files._get_path_mountpath(args)
        file_mount = self.files._get_path_mountfile(args, template)
        dir_intermediate = self.files._get_path_intermediate(args)
        self.files.unmount_folder(dir_mount)
        if self.files.mount_folder(file_mount, dir_mount):
            os.makedirs(dir_intermediate, exist_ok=True)
            copied = self.files.copy_folder_iso(dir_mount, dir_intermediate)
            copied = self.files.chmod(dir_intermediate, privilege=0o200)
            self.files.unmount_folder(dir_mount)
            if copied:
                log_info(f"Copied ISO    : {file_mount}")
                return True
        return False

    def _ensure_task_iso(self, args: TaskConfig, template: TemplateConfig) -> bool:
        fullname = self.files._get_path_isosource(args, template)
        if self.exists(fullname):
            log_info("Download ISO  : Already present")
            return True
        log_info(f"Download ISO  : {fullname}")
        return self._download_file(args, template)

    def _get_task_template(self, args: TaskConfig) -> Optional[TemplateConfig]:
        name = args.target.template
        if name in self.templates.keys():
            return self.templates[name]
        return None
