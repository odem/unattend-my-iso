import os
import glob
import re
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.helpers.config import IsoTemplate, TaskConfig
from unattend_my_iso.helpers.logging import log_debug


class GrubAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "grub")

    def _get_kernel_version(self, path: str) -> str:
        pattern = f"{path}/pool/main/l/linux/linux-headers-*_all.deb"
        files = glob.glob(pattern)
        version_regex = re.compile(r"linux-headers-(\d+\.\d+\.\d+-\d+)-common")
        for file in files:
            match = version_regex.search(file)
            if match:
                kernel_version = match.group(1)
                return kernel_version
        return "X.Y.Z-W"

    @override
    def integrate_addon(self, args: TaskConfig, template: IsoTemplate) -> bool:
        templatepath = args.sys.template_path
        templatename = args.target.template
        interpath = args.sys.intermediate_path
        intername = args.target.template
        src = f"{templatepath}/{templatename}"
        dst = f"{interpath}/{intername}"
        dstgrub = f"{dst}/boot/grub"
        srcgrub = f"{src}/{template.path_grub}"
        kernel = self._get_kernel_version(dst)
        log_debug(f"Found kernel  : {kernel}")
        log_debug(f"Integrated    : {self.addon_name}")
        os.makedirs(dstgrub, exist_ok=True)
        if self.files.copy_folder(f"{srcgrub}/themes", dstgrub) is False:
            return False
        if self.files.copy_file(f"{srcgrub}/grub.cfg", dstgrub) is False:
            return False
        log_debug(f"Integrated    : {self.addon_name}")
        return True
