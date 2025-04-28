import os
import re
import glob
from abc import ABC, abstractmethod
from unattend_my_iso.common.logging import log_debug, log_error
from unattend_my_iso.common.model import Replaceable
from unattend_my_iso.core.files.file_manager import UmiFileManager
from unattend_my_iso.common.config import TaskConfig, TemplateConfig


class UmiAddon(ABC):

    addon_name: str
    replacements: list[Replaceable]

    def __init__(self, name: str):
        self.addon_name = name
        self.files = UmiFileManager()
        self.replacements = []

    def get_template_path_optional(
        self, addon: str, subpath: str, args: TaskConfig
    ) -> str:
        srctmpl = self.files._get_path_template(args)
        srcaddon = self.files._get_path_template_addon(addon, args)
        srcsub = f"{srctmpl}/{addon}/{subpath}"

        if subpath != "":
            if os.path.exists(srcsub) is False:
                srcsub = f"{srcaddon}/{subpath}"
                if os.path.exists(srcsub) is False:
                    log_error(f"No optional template path : {srcsub}", "AddonBase")
                    return ""
        return srcsub

    def _extract_kernel_version_image(self, path: str) -> str:
        searchfolder = f"{path}/pool/main/l/linux-signed-amd64"
        pattern = f"{searchfolder}/linux-image-*-amd64_*.deb"
        files = glob.glob(pattern)
        version_regex = re.compile(r"linux-image-(\d+\.\d+\.\d+-\d+)-amd*")
        for file in files:
            match = version_regex.search(file)
            if match:
                kernel_version = match.group(1)
                return kernel_version
        return "X.Y.Z-W"

    def _extract_kernel_version_headers(self, path: str) -> str:
        searchfolder = f"{path}/pool/main/l"
        pattern = f"{searchfolder}/linux-headers-*_all.deb"
        files = glob.glob(pattern)
        version_regex = re.compile(r"linux-headers-(\d+\.\d+\.\d+-\d+)-common")
        for file in files:
            match = version_regex.search(file)
            if match:
                kernel_version = match.group(1)
                return kernel_version
        return "X.Y.Z-W"

    def _extract_kernel_version(self, path: str) -> str:
        kernel = self._extract_kernel_version_headers(path)
        if kernel == "X.Y.Z-W":
            kernel = self._extract_kernel_version_image(path)
        if kernel == "X.Y.Z-W":
            log_debug(f"Kernelversion not extracted: {path}", "AddonBase")
        return kernel

    def _apply_replacements(self, replacements: list[Replaceable]) -> bool:
        for rule in replacements:
            self.replacements.append(rule)
        return self.do_replacements()

    def do_replacements(self) -> bool:
        for rule in self.replacements:
            self.files.replace_string(rule.filename, rule.searchterm, rule.replacement)
        return True

    @abstractmethod
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        raise NotImplementedError("Not implemented")
