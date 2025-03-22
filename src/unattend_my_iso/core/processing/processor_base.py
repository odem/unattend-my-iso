import os
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
from unattend_my_iso.common.logging import log_debug
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
        self.templates = read_templates_isos(self.sysconfig.template_path)
        log_debug("Enumerate Templates:")
        for t in self.templates.values():
            log_debug(f" -- Template:  {t.name}")

    def _download_file(self, args: TaskConfig, url: str, name: str) -> bool:
        fullname = self.files._get_path_isofile(args)
        self.files.http_download(url=url, name=name, dir=self.sysconfig.iso_path)
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
        log_debug(f"  Templates -> {args.sys.template_path}")
        log_debug(f"  Mounts    -> {args.sys.mnt_path }")
        log_debug(f"  out       -> {args.sys.intermediate_path}")
        log_debug(f"  Iso       -> {args.sys.iso_path}")
