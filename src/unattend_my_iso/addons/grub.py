import os
import glob
import re
from datetime import datetime
from typing_extensions import override
from unattend_my_iso.addons.addon_base import Replaceable, UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug


class GrubAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "grub")

    def _extract_kernel_version_image(self, path: str) -> str:
        pattern = f"{path}/pool/main/l/linux-signed-amd64/linux-image-*-amd64_*.deb"
        files = glob.glob(pattern)
        version_regex = re.compile(r"linux-image-(\d+\.\d+\.\d+-\d+)-amd*")
        for file in files:
            match = version_regex.search(file)
            if match:
                kernel_version = match.group(1)
                log_debug("Extracted kernel version via image")
                return kernel_version
        return "X.Y.Z-W"

    def _extract_kernel_version_headers(self, path: str) -> str:
        pattern = f"{path}/pool/main/l/linux/linux-headers-*_all.deb"
        files = glob.glob(pattern)
        version_regex = re.compile(r"linux-headers-(\d+\.\d+\.\d+-\d+)-common")
        for file in files:
            match = version_regex.search(file)
            if match:
                kernel_version = match.group(1)
                log_debug("Extracted kernel version via header")
                return kernel_version
        return "X.Y.Z-W"

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        src = self.files._get_path_template(args)
        dst = self.files._get_path_intermediate(args)
        dstboot = f"{dst}/boot"
        dstgrub = f"{dstboot}/grub"
        defaultgrub = f"{dstgrub}/themes/default"
        srcgrub = f"{src}/{template.path_grub}"
        srcicons = f"{srcgrub}/icons/{args.addons.grub.grub_icons}"
        dstthemes = f"{dstgrub}/themes"
        dstiso = f"{dstboot}/iso"
        dsticons = f"{dstgrub}/themes/{args.addons.grub.grub_theme}/icons"
        dstthemefile = f"{dstgrub}/themes/{args.addons.grub.grub_theme}/theme.txt"
        grubfile = f"{dstgrub}/grub.cfg"
        os.makedirs(dstiso, exist_ok=True)
        os.makedirs(dstthemes, exist_ok=True)
        self.files.mv(f"{dstgrub}/theme", f"{dstgrub}/themes/default")
        self.files.mv(f"{defaultgrub}/1", f"{defaultgrub}/theme.txt")
        if self.files.cp(f"{srcgrub}/themes", dstthemes) is False:
            return False
        if (
            args.addons.grub.grub_icons != ""
            and self.files.cp(f"{srcicons}", dsticons) is False
        ):
            return False
        if self.files.cp(f"{srcgrub}/grub.cfg", dstgrub) is False:
            return False
        if self.files.cp("/boot/memtest86+x64.bin", dstboot) is False:
            return False
        if self.files.cp("/boot/memtest86+x64.efi", dstboot) is False:
            return False
        return self._apply_replacements(args, dst, grubfile, dstthemefile)

    def _apply_replacements(
        self, args: TaskConfig, inter: str, grub: str, themefile: str
    ) -> bool:
        kernel = self._extract_kernel_version_headers(inter)
        if kernel == "X.Y.Z-W":
            kernel = self._extract_kernel_version_image(inter)

        name = args.target.template
        hostname = args.addons.answerfile.host_name
        domain = args.addons.answerfile.host_domain
        ip = args.addons.answerfile.net_ip
        version = args.sys.tool_version
        timeout = args.addons.grub.timeout
        theme = args.addons.grub.grub_theme
        sleeptime = args.addons.grub.sleeptime
        buildtime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rules = [
            Replaceable(grub, "CFG_THEME", theme),
            Replaceable(grub, "CFG_KERNEL", kernel),
            Replaceable(grub, "CFG_TYPE", name),
            Replaceable(grub, "CFG_HOST", hostname),
            Replaceable(grub, "CFG_IP", ip),
            Replaceable(grub, "CFG_BUILDTIME", buildtime),
            Replaceable(grub, "CFG_VERSION", version),
            Replaceable(grub, "CFG_SLEEPTIME", str(sleeptime)),
            Replaceable(grub, "CFG_TIMEOUT", str(timeout)),
            Replaceable(themefile, "CFG_TYPE", name),
            Replaceable(themefile, "CFG_HOST", hostname),
            Replaceable(themefile, "CFG_DOMAIN", domain),
            Replaceable(themefile, "CFG_IP", hostname),
            Replaceable(themefile, "CFG_KERNEL", kernel),
            Replaceable(themefile, "CFG_VERSION", version),
        ]
        for rule in rules:
            self.replacements.append(rule)
        return self.do_replacements()
