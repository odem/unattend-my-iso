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
        dstthemefile = f"{dsttheme}/theme.txt"
        if template.iso_type == "windows":
            postfolder = f"{srctmpl}/{template.path_postinstall}"
            postfile = f"{dstpost}/postinstall.bat"
        else:
            postfolder = f"{srctmpl}/{template.path_postinstall}"
            postfile = f"{dstpost}/postinstall.bash"
            if args.addons.postinstall.enable_grub_theme:
                os.makedirs(dsttheme, exist_ok=True)
                log_debug(f"LOG_DEBUG: {srctheme} -> {dsttheme}")
                if self.files.cp(srctheme, dsttheme) is False:
                    return False
                rules = self._create_replacements_theme(args, dstthemefile)
                if self._apply_replacements(rules) is False:
                    return False
        if self.files.cp(postfolder, dstpost) is False:
            return False
        if self._create_config(args) is False:
            return False
        rules = self._create_replacements_postinst(args, postfile)
        if self._apply_replacements(rules) is False:
            return False
        return True

    def _create_config(self, args: TaskConfig) -> bool:
        interpath = args.sys.intermediate_path
        intername = args.target.template
        dst = f"{interpath}/{intername}/umi"
        dstconf = f"{dst}/config"
        dstconffile = f"{dstconf}/env.bash"
        os.makedirs(dstconf, exist_ok=True)
        name = args.target.template
        hostname = args.addons.answerfile.host_name
        domain = args.addons.answerfile.host_domain
        version = args.sys.tool_version
        arr = [
            "#!/bin/bash",
            f"CFG_TYPE={name}",
            f"CFG_HOST={hostname}",
            f"CFG_DOMAIN={domain}",
            f"CFG_VERSION={version}",
        ]
        contents = "\n".join(arr)
        if os.path.exists(dstconffile):
            self.files.rm(dstconffile)
        if self.files.append_to_file(dstconffile, contents) is False:
            return False
        return self.files.chmod(dstconffile, 777)

    def _create_replacements_theme(
        self, args: TaskConfig, themefile: str
    ) -> list[Replaceable]:
        name = args.target.template
        hostname = args.addons.answerfile.host_name
        domain = args.addons.answerfile.host_domain
        version = args.sys.tool_version
        dst = self.files._get_path_intermediate(args)
        kernel = self._extract_kernel_version(dst)
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

    def _create_replacements_postinst(
        self, args: TaskConfig, postinst: str
    ) -> list[Replaceable]:
        c = args.addons.answerfile
        return [
            Replaceable(postinst, "CFG_USER_OTHER_NAME", c.user_other_name),
        ]
