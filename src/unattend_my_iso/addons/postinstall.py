import os
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug
from unattend_my_iso.common.model import Replaceable


class PostinstallAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "postinstall")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        templatepath = args.sys.template_path
        templatename = args.target.template
        interpath = args.sys.intermediate_path
        intername = args.target.template
        srctmpl = f"{templatepath}/{templatename}"
        srctheme = f"{srctmpl}/grub/themes/{args.addons.grub.grub_theme}"
        dst = f"{interpath}/{intername}/umi"
        dstpost = f"{dst}/postinstall"
        dsttheme = f"{dst}/theme"
        os.makedirs(dsttheme, exist_ok=True)
        log_debug(f"LOG_DEBUG: {srctheme} -> {dsttheme}")
        if self.files.cp(srctheme, dsttheme) is False:
            return False
        if template.iso_type == "windows":
            postfolder = f"{srctmpl}/{template.path_postinstall}"
            postfile = f"{dstpost}/postinstall.bat"
        else:
            postfolder = f"{srctmpl}/{template.path_postinstall}"
            postfile = f"{dstpost}/postinstall.bash"
        if self.files.cp(postfolder, dstpost) is False:
            return False
        return self._apply_replacements(args, postfile)

    def _apply_replacements(self, args: TaskConfig, postinst: str) -> bool:
        c = args.addons.answerfile
        rules = [
            Replaceable(postinst, "CFG_USER_OTHER_NAME", c.user_other_name),
        ]
        for rule in rules:
            self.replacements.append(rule)
        return self.do_replacements()
