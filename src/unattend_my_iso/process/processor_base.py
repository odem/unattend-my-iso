import os
import subprocess
from unattend_my_iso.helpers.config import (
    IsoTemplate,
    TaskConfig,
    TaskResult,
    create_default_config,
    read_templates_isos,
)
from unattend_my_iso.helpers.downloads import download_file
from unattend_my_iso.helpers.logging import log_debug
from unattend_my_iso.helpers.mount import mount_folder, unmount_folder
from unattend_my_iso.helpers.sys import get_cwd


class TaskProcessorBase:
    work_path: str
    taskconfig: TaskConfig
    templates: dict[str, IsoTemplate]

    def __init__(self, work_path: str = ""):
        self.work_path = work_path
        self._get_templates()

    def exists(self, path: str) -> bool:
        if os.path.exists(path):
            return True
        return False

    def _mount_folder(self, src: str, name: str, dst: str) -> bool:
        return mount_folder(src, name, dst)

    def _unmount_folder(self, dir: str) -> bool:
        return unmount_folder(dir)

    def _download_file(self, template: IsoTemplate) -> bool:
        if download_file(
            url=template.iso_url,
            name=template.iso_name,
            dir=self.taskconfig.sys.iso_path,
        ):
            return True
        return False

    def _get_templates(self):
        if self.work_path == "":
            self.work_path = get_cwd()
        self.taskconfig = create_default_config(work_path=self.work_path)
        self.templates = read_templates_isos(self.taskconfig.sys.template_path)
        log_debug("Enumerate Templates:")
        for t in self.templates.values():
            log_debug(f" -- Template:  {t.name}")

    def _get_success_result(self, msg: str = ""):
        return TaskResult(True, msg=msg, msg_short="", msg_out="", msg_err="")

    def _get_error_result(
        self, msg: str, msg_short: str = "", msg_out: str = "", msg_err: str = ""
    ):
        return TaskResult(
            True, msg=msg, msg_short=msg_short, msg_out=msg_out, msg_err=msg_err
        )

    def _print_args(self, args: TaskConfig):
        log_debug(f"Addons: {args.addons}")
        log_debug(f"Target: {args.target}")
        log_debug("System:")
        log_debug(f"  Templates -> {args.sys.template_path}")
        log_debug(f"  Mounts    -> {args.sys.mnt_path }")
        log_debug(f"  out       -> {args.sys.intermediate_path}")
        log_debug(f"  Iso       -> {args.sys.iso_path}")
