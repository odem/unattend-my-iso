import os
from typing import Optional
from unattend_my_iso.addons.answerfile import AnswerFileAddon
from unattend_my_iso.addons.grub import GrubAddon
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.addons.postinstall import PostinstallAddon
from unattend_my_iso.addons.ssh import SshAddon
from unattend_my_iso.common.common import TaskResult
from unattend_my_iso.common.templates import read_templates_isos
from unattend_my_iso.core.files.file_manager import UmiFileManager
from unattend_my_iso.core.iso.iso_generator import UmiIsoGenerator
from unattend_my_iso.core.vm.hypervisor_base import UmiHypervisorBase
from unattend_my_iso.core.vm.hypervisor_kvm import UmiHypervisorKvm
from unattend_my_iso.common.logging import log_debug, log_error, log_info
from unattend_my_iso.common.config import (
    SysConfig,
    TaskConfig,
    TemplateConfig,
    get_cfg_sys,
)


class TaskProcessorBase:
    work_path: str
    sysconfig: SysConfig
    templates: dict[str, TemplateConfig] = {}
    addons: dict[str, UmiAddon] = {}
    files: UmiFileManager = UmiFileManager()
    isogen: UmiIsoGenerator = UmiIsoGenerator()
    hvrunner: UmiHypervisorBase = UmiHypervisorKvm()

    def __init__(self, work_path: str = ""):
        self.work_path = work_path
        if self.work_path == "":
            self.work_path = self.files.cwd()
        self.sysconfig = get_cfg_sys(work_path=self.work_path)
        self._get_addons()
        self._get_templates()

    def _create_efidisk_windows(self, args: TaskConfig) -> bool:
        dstinter = self.files._get_path_intermediate(args)
        try:
            if self.isogen.create_efidisk_windows(args, dstinter) is False:
                log_error(f"Error creating efidisk for windows: {dstinter}")
                return False
        except Exception as exe:
            log_error(f"Exception on efidisk: {exe}")
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
                    log_info(f"Skipped irmod: {initrd}")
        except Exception as exe:
            log_error(f"Exception on irmod: {exe}")
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
                    matches.append(filepath)
        return matches

    def _copy_addon(
        self, name: str, args: TaskConfig, template: TemplateConfig
    ) -> bool:
        addon = self.addons[name]
        success = addon.integrate_addon(args, template)
        log_info(f"Addon update : {addon.addon_name} -> {success}")
        return success

    def _get_addons(self):
        grub = GrubAddon()
        ssh = SshAddon()
        postinst = PostinstallAddon()
        answer = AnswerFileAddon()
        self.addons = {
            answer.addon_name: answer,
            grub.addon_name: grub,
            ssh.addon_name: ssh,
            postinst.addon_name: postinst,
        }

    def _get_templates(self):
        searchpath = f"{self.sysconfig.path_templates}/iso"
        self.templates = read_templates_isos(searchpath)

    def _get_task_template(self, args: TaskConfig) -> Optional[TemplateConfig]:
        name = args.target.template
        if name in self.templates.keys():
            return self.templates[name]
        return None

    def _download_file(self, args: TaskConfig, url: str, name: str) -> bool:
        fullname = self.files._get_path_isofile(args)
        self.files.http_download(url=url, name=name, dir=self.sysconfig.path_iso)
        return self.exists(fullname)

    def _get_success_result(self, msg: str = ""):
        return TaskResult(True, msg=msg, msg_short="", msg_out="", msg_err="")

    def _get_error_result(
        self, msg: str, msg_short: str = "", msg_out: str = "", msg_err: str = ""
    ):
        return TaskResult(
            True, msg=msg, msg_short=msg_short, msg_out=msg_out, msg_err=msg_err
        )

    def exists(self, path: str) -> bool:
        if os.path.exists(path):
            return True
        return False

    def _print_args(self, args: TaskConfig):
        log_debug(f"Addons: {args.addons}")
        log_debug(f"Target: {args.target}")
        log_debug("System:")
        log_debug(f"  Templates -> {args.sys.path_templates}")
        log_debug(f"  Mounts    -> {args.sys.path_mnt }")
        log_debug(f"  out       -> {args.sys.path_intermediate}")
        log_debug(f"  Iso       -> {args.sys.path_iso}")
