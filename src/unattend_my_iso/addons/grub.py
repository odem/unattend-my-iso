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
        if self.copy_grub(args, template) is False:
            return False
        if self.copy_theme(args, template) is False:
            return False
        if self.copy_memtest(args) is False:
            return False
        return True

    def copy_grub(self, args: TaskConfig, template: TemplateConfig) -> bool:
        srcgrub = self.get_template_path_optional("grub", "grub.cfg", args)
        dst = self.files._get_path_intermediate(args)
        dstgrub = f"{dst}/boot/grub"
        dstgrubfile = f"{dstgrub}/grub.cfg"
        if self.files.cp(srcgrub, dstgrub) is False:
            return False
        rules = self._create_replacements_grub(args, dst, dstgrubfile)
        return self._apply_replacements(rules)

    def copy_theme(self, args: TaskConfig, template: TemplateConfig) -> bool:
        dst = self.files._get_path_intermediate(args)
        themename = args.addons.grub.grub_theme
        themeicons = args.addons.grub.grub_icons
        themename = args.addons.grub.grub_theme
        srctheme = self.get_template_path_optional("grub", f"themes/{themename}", args)
        srcicons = self.get_template_path_optional("grub", f"icons/{themeicons}", args)
        dstgrub = f"{dst}/boot/grub"
        dstthemes = f"{dstgrub}/themes"
        dsticons = f"{dstthemes}/{themename}/icons"
        dstthemefile = f"{dstthemes}/{themename}/theme.txt"
        if themename != "":
            if self.files.cp(srctheme, f"{dstthemes}/{themename}") is False:
                return False
            if self.move_default_theme(args) is False:
                return False
            if (
                args.addons.grub.grub_icons != ""
                and self.files.cp(srcicons, dsticons) is False
            ):
                return False
            rules = self._create_replacements_theme(args, dst, dstthemefile)
            return self._apply_replacements(rules)
        return True

    def move_default_theme(self, args: TaskConfig) -> bool:
        dst = self.files._get_path_intermediate(args)
        dstgrub = f"{dst}/boot/grub"
        dstthemes = f"{dstgrub}/themes"
        dstdefault = f"{dstthemes}/default"
        os.makedirs(dstthemes, exist_ok=True)
        if self.files.mv(f"{dstgrub}/theme", f"{dstdefault}") is False:
            return False
        if self.files.mv(f"{dstdefault}/1", f"{dstdefault}/theme.txt") is False:
            return False
        return True

    def copy_memtest(self, args: TaskConfig) -> bool:
        dst = self.files._get_path_intermediate(args)
        dstboot = f"{dst}/boot"
        if self.files.cp("/boot/memtest86+x64.bin", dstboot) is False:
            return False
        if self.files.cp("/boot/memtest86+x64.efi", dstboot) is False:
            return False
        return True

    def _create_replacements_grub(
        self, args: TaskConfig, inter: str, grub: str
    ) -> list[Replaceable]:
        kernel = self._extract_kernel_version_headers(inter)
        if kernel == "X.Y.Z-W":
            kernel = self._extract_kernel_version_image(inter)
        name = args.target.template
        hostname = args.addons.answerfile.host_name
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
        return rules

    def _create_replacements_theme(
        self, args: TaskConfig, inter: str, themefile: str
    ) -> list[Replaceable]:
        kernel = self._extract_kernel_version_headers(inter)
        if kernel == "X.Y.Z-W":
            kernel = self._extract_kernel_version_image(inter)
        name = args.target.template
        hostname = args.addons.answerfile.host_name
        domain = args.addons.answerfile.host_domain
        version = args.sys.tool_version
        rules = []
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
