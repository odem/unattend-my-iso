import os
from typing import Optional
from unattend_my_iso.addons.answerfile import AnswerFileAddon
from unattend_my_iso.addons.grub import GrubAddon
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.addons.postinstall import PostinstallAddon
from unattend_my_iso.addons.ssh import SshAddon
from unattend_my_iso.common.templates import read_templates_isos
from unattend_my_iso.core.files.file_manager import UmiFileManager
from unattend_my_iso.core.generators.generator_iso import UmiIsoGenerator
from unattend_my_iso.core.net.net_manager import UmiNetworkManager
from unattend_my_iso.core.reader.reader_toml import TomlReader
from unattend_my_iso.core.vm.hypervisor_base import UmiHypervisorBase
from unattend_my_iso.core.vm.hypervisor_kvm import UmiHypervisorKvm
from unattend_my_iso.common.logging import log_error, log_info
from unattend_my_iso.common.config import (
    SysConfig,
    TaskConfig,
    TemplateConfig,
    get_cfg_sys,
    TaskResult,
)


class TaskProcessorBase:
    work_path: str
    sysconfig: SysConfig
    templates: dict[str, TemplateConfig] = {}
    addons: dict[str, UmiAddon] = {}
    files: UmiFileManager = UmiFileManager()
    isogen: UmiIsoGenerator = UmiIsoGenerator()
    hvrunner: UmiHypervisorBase = UmiHypervisorKvm()
    netman: UmiNetworkManager = UmiNetworkManager()

    def __init__(self, work_path: str = ""):
        self.work_path = work_path
        if self.work_path == "":
            self.work_path = self.files.cwd()
        self.sysconfig = get_cfg_sys(work_path=self.work_path)
        self._get_addons()
        self._get_templates()
        self._get_overlays()

    def _create_efidisk_windows(self, args: TaskConfig) -> bool:
        dstinter = self.files._get_path_intermediate(args)
        try:
            if self.isogen.create_efidisk_windows(args, dstinter) is False:
                log_error(
                    f"Error creating efidisk for windows: {dstinter}",
                    self.__class__.__qualname__,
                )
                return False
        except Exception as exe:
            log_error(f"Exception on efidisk: {exe}", self.__class__.__qualname__)
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
                        log_error(
                            f"Error creating irmod: {subdir}",
                            self.__class__.__qualname__,
                        )
                        return False
                else:
                    log_info(f"Skipped irmod: {initrd}", self.__class__.__qualname__)
        except Exception as exe:
            log_error(f"Exception on irmod: {exe}", self.__class__.__qualname__)
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

    def _integrate_addon(
        self, name: str, args: TaskConfig, template: TemplateConfig
    ) -> bool:
        addon = self.addons[name]
        success = addon.integrate_addon(args, template)
        log_info(
            f"Integrated addon {addon.addon_name} -> {success}",
            self.__class__.__qualname__,
        )
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

    def _get_overlays(self):
        self.overlays = {}
        searchpath = f"{self.sysconfig.path_templates}/iso"
        for template in self.templates.values():
            for overlay in template.files_overlay:
                name = ""
                if overlay.startswith("desc.") and overlay.endswith(".toml"):
                    arr = overlay.split(".")
                    name = arr[1]
                descfile = f"{searchpath}/{template.name}/desc.{name}.toml"
                obj_overlay = TemplateConfig(**template.__dict__)
                reader = TomlReader()
                overlay_toml = reader.read_toml_file(descfile)
                if overlay_toml is not None and "description" in overlay_toml:
                    overlay_desc = overlay_toml["description"]
                    for fld in overlay_desc.items():
                        fld_name = fld[0]
                        fld_val = fld[1]
                        setattr(obj_overlay, fld_name, fld_val)
                    setattr(obj_overlay, "name_overlay", name)
                    overlay_name = f"{template.name}.{name}"
                    self.overlays[overlay_name] = obj_overlay

    def _get_task_template(self, args: TaskConfig) -> Optional[TemplateConfig]:
        ret = None
        name = args.target.template
        overlay = args.target.template_overlay
        combined = f"{name}.{overlay}"
        if overlay == "":
            if name in self.templates.keys():
                ret = self.templates[name]
        else:
            if combined in self.overlays.keys():
                overlay = self.overlays[combined]
                ret = self.overlays[combined]
        return ret

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
