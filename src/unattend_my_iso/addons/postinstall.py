import os
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error
from unattend_my_iso.common.model import Replaceable


class PostinstallAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "postinstall")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if self.copy_postinstall(args, template) is False:
            return False
        if self.copy_postinstaller_additional_scripts(args, template) is False:
            return False
        if self._copy_bashrc(args) is False:
            return False
        if self.copy_theme(args, template) is False:
            return False
        if self._create_config(args) is False:
            return False
        return True

    def copy_postinstall(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if self.copy_postinstaller_dir(args, template) is False:
            return False
        postfile = self.copy_postinstaller_file(args, template)
        if postfile == "":
            return False
        rules = self._create_replacements_postinst(args, postfile)
        if self._apply_replacements(rules) is False:
            return False
        return True

    def copy_postinstaller_file(
        self, args: TaskConfig, template: TemplateConfig
    ) -> str:
        srctmpl = self.files._get_path_template(args)
        srcaddon = self.files._get_path_template_addon("postinstall", args)
        interpath = self.files._get_path_intermediate(args)
        postfile = f"{srctmpl}/{template.file_postinstall}"
        dst = f"{interpath}/umi/postinstall"
        dstfile = f"{dst}/{template.file_postinstall}"
        if os.path.exists(postfile) is False:
            postfile = f"{srcaddon}/{template.file_postinstall}"
        if template.file_postinstall != "" and os.path.exists(postfile) is False:
            log_error("Postinstall file does not exist")
            return ""
        if self.files.cp(postfile, dstfile) is False:
            return ""
        return postfile

    def copy_postinstaller_dir(
        self, args: TaskConfig, template: TemplateConfig
    ) -> bool:
        srcpath = self.get_template_path_optional("postinstall", "", args)
        interpath = self.files._get_path_intermediate(args)
        dstdir = f"{interpath}/umi/{template.path_postinstall}"
        os.makedirs(dstdir, exist_ok=True)
        if template.path_postinstall != "":
            if os.path.exists(srcpath):
                if self.files.cp(srcpath, dstdir) is False:
                    log_error("Postinstall copy failed")
                    return False
            else:
                log_error(f"Invalid src path: {srcpath}")
                return False
        return True

    def copy_postinstaller_additional_scripts(
        self, args: TaskConfig, template: TemplateConfig
    ) -> bool:
        interpath = self.files._get_path_intermediate(args)
        dst = f"{interpath}/umi/postinstall"

        for filename in args.addons.postinstall.copy_additional_scripts:
            srcpath = self.get_template_path_optional("postinstall", filename, args)
            dstfile = f"{interpath}/umi/postinstall/{filename}"
            if template.path_postinstall != "":
                if os.path.exists(srcpath):
                    os.makedirs(dst, exist_ok=True)
                    if self.files.cp(srcpath, dstfile) is False:
                        log_error("Postinstall copy failed")
                        return False
        return True

    def copy_theme(self, args: TaskConfig, template: TemplateConfig) -> bool:
        srcpath = self.get_template_path_optional(
            "grub", f"themes/{args.addons.grub.grub_theme}", args
        )
        interpath = self.files._get_path_intermediate(args)
        dst = f"{interpath}/umi/theme"
        dstthemefile = f"{dst}/theme.txt"
        if template.iso_type == "windows":
            return True

        if args.addons.postinstall.enable_grub_theme:
            if os.path.exists(srcpath) is False:
                log_error(f"Themefiles not available: {args.addons.grub.grub_theme}")
                return False
            if os.path.exists(srcpath):
                os.makedirs(dst, exist_ok=True)
            if self.files.cp(srcpath, dst) is False:
                return False
            rules = self._create_replacements_theme(args, dstthemefile)
            if self._apply_replacements(rules) is False:
                return False
        return True

    def _create_config(self, args: TaskConfig) -> bool:
        if args.addons.postinstall.create_config is False:
            return True
        interpath = self.files._get_path_intermediate(args)
        dstconf = f"{interpath}/umi/config"
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

    def _copy_bashrc(self, args: TaskConfig) -> bool:
        if args.addons.postinstall.bashrc_file == "":
            return True
        srcfile = self.get_template_path_optional(
            "postinstall", args.addons.postinstall.bashrc_file, args
        )
        if os.path.exists(srcfile):
            interpath = self.files._get_path_intermediate(args)
            dstconf = f"{interpath}/umi/config"
            dstconffile = f"{dstconf}/{args.addons.postinstall.bashrc_file}"
            os.makedirs(dstconf, exist_ok=True)
            return self.files.cp(srcfile, dstconffile)
        return False

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
