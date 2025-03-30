import os
from datetime import datetime
from typing_extensions import override
from unattend_my_iso.addons.addon_base import Replaceable, UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig


class GrubAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "grub")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if template.iso_type == "windows":
            return True

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
        rules = self._create_replacements(args, dst, grubfile, dstthemefile)
        return self._apply_replacements(rules)

    def _create_replacements(
        self, args: TaskConfig, inter: str, grub: str, themefile: str
    ) -> list[Replaceable]:
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
        rules = []
        if os.path.exists(grub):
            rules += [
                Replaceable(grub, "CFG_THEME", theme),
                Replaceable(grub, "CFG_KERNEL", kernel),
                Replaceable(grub, "CFG_TYPE", name),
                Replaceable(grub, "CFG_HOST", hostname),
                Replaceable(grub, "CFG_IP", ip),
                Replaceable(grub, "CFG_BUILDTIME", buildtime),
                Replaceable(grub, "CFG_VERSION", version),
                Replaceable(grub, "CFG_SLEEPTIME", str(sleeptime)),
                Replaceable(grub, "CFG_TIMEOUT", str(timeout)),
            ]
        if os.path.exists(themefile):
            rules += [
                Replaceable(themefile, "CFG_TYPE", name),
                Replaceable(themefile, "CFG_HOST", hostname),
                Replaceable(themefile, "CFG_DOMAIN", domain),
                Replaceable(themefile, "CFG_IP", hostname),
                Replaceable(themefile, "CFG_KERNEL", kernel),
                Replaceable(themefile, "CFG_VERSION", version),
            ]
        return rules
