import os
import glob
import re
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug


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
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        templatepath = args.sys.template_path
        templatename = args.target.template
        interpath = args.sys.intermediate_path
        intername = args.target.template
        src = f"{templatepath}/{templatename}"
        dst = f"{interpath}/{intername}"
        dstgrub = f"{dst}/boot/grub"
        dstthemes = f"{dstgrub}/themes"
        srcgrub = f"{src}/{template.path_grub}"
        kernel = self._get_kernel_version(dst)
        log_debug(f"Found kernel : {kernel}")
        os.makedirs(dstthemes, exist_ok=True)
        self.files.mv(f"{dstgrub}/theme", f"{dstgrub}/themes/default")
        if self.files.cp(f"{srcgrub}/themes", dstthemes) is False:
            return False
        if self.files.cp(f"{srcgrub}/grub.cfg", dstgrub) is False:
            return False
        return True
