import os
import random
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error, log_info
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
        # if self._copy_bashrc(args) is False:
        #     return False
        if self._copy_bash_aliases(args, template) is False:
            return False
        if self.copy_theme(args, template) is False:
            return False
        if self._create_config(args, template) is False:
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
        interpath = self.files._get_path_intermediate(args)
        postfile = self.get_template_path_optional(
            "postinstall", template.file_postinstall, args
        )
        dst = f"{interpath}/umi/postinstall"
        dstfile = f"{dst}/{template.file_postinstall}"
        if os.path.exists(dst) is False:
            os.makedirs(dst)
        if template.file_postinstall != "" and os.path.exists(postfile) is False:
            log_error("Postinstall file does not exist", self.__class__.__qualname__)
            return ""
        if self.files.cp(postfile, dstfile) is False:
            return ""
        return dstfile

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
                    log_error("Postinstall copy failed", self.__class__.__qualname__)
                    return False
            else:
                log_error(f"Invalid path : {srcpath}", self.__class__.__qualname__)
                return False
        return True

    def copy_postinstaller_additional_scripts(
        self, args: TaskConfig, template: TemplateConfig
    ) -> bool:
        interpath = self.files._get_path_intermediate(args)

        allscripts = [
            *args.addons.postinstall.copy_additional_scripts,
            *args.addons.postinstall.exec_additional_scripts,
        ]
        for filename in allscripts:
            log_debug(f"Copy File {filename}", self.__class__.__qualname__)
            srcpath = self.get_template_path_optional("postinstall", filename, args)
            dstfile = f"{interpath}/umi/postinstall/{filename}"
            dstpath = os.path.dirname(dstfile)
            if os.path.exists(srcpath):
                os.makedirs(dstpath, exist_ok=True)
                if self.files.cp(srcpath, dstfile) is False:
                    log_error("Postinstall copy failed", self.__class__.__qualname__)
                    return False
            else:
                log_error(
                    "Postinstall file does not exist", self.__class__.__qualname__
                )
                return False
        return True

    def copy_theme(self, args: TaskConfig, template: TemplateConfig) -> bool:
        interpath = self.files._get_path_intermediate(args)
        dst = f"{interpath}/umi/theme"
        dstthemefile = f"{dst}/theme.txt"
        if template.iso_type == "windows":
            return True

        if args.addons.postinstall.enable_grub_theme:
            if args.addons.grub.grub_theme == "default":
                return True
            srcpath = self.get_template_path_optional(
                "grub", f"themes/{args.addons.grub.grub_theme}", args
            )
            if os.path.exists(srcpath) is False:
                log_error(
                    f"Themefiles not available: {args.addons.grub.grub_theme}",
                    "Postinstall",
                )
                return False
            if os.path.exists(srcpath):
                os.makedirs(dst, exist_ok=True)
            if self.files.cp(srcpath, dst) is False:
                return False
            rules = self._create_replacements_theme(args, dstthemefile)
            if self._apply_replacements(rules) is False:
                return False
        return True

    def _create_params_list_bash(self, elements: list, prefix: str = ""):
        joblist_arg = []
        for script in elements:
            entry = f'"{prefix}{script}"'
            joblist_arg.append(entry)
        return joblist_arg

    def _create_params_list_batch(self, elements: list, prefix: str = ""):
        joblist_arg = []
        for script in elements:
            entry = f'"{prefix}{script}"'
            joblist_arg.append(entry)
        return joblist_arg

    def _create_params_env(self, elements: list, name: str, prefix: str = ""):
        joblist_arg = ["("]
        joblist_arg += self._create_params_list_bash(elements, prefix)
        joblist_arg += [")"]
        return f"{name}={' '.join(joblist_arg)}"

    def _create_params_alljobs_bash(self, args: TaskConfig, name: str = ""):
        joblist_arg = ["("]
        post = args.addons.postinstall
        joblist_arg += self._create_params_list_bash(post.joblist_early)
        joblist_arg += self._create_params_list_bash(
            post.exec_additional_scripts, "/opt/umi/postinstall/"
        )
        joblist_arg += self._create_params_list_bash(post.joblist_late)
        joblist_arg += [")"]
        result = " ".join(joblist_arg)
        if name != "":
            result = f"{name}={result}"
        return result

    def _create_params_alljobs_batch(self, args: TaskConfig, name: str = ""):

        result = ""

        post = args.addons.postinstall
        joblist_arg = []
        joblist_arg += self._create_params_list_batch(post.joblist_early)
        joblist_arg += self._create_params_list_batch(
            post.exec_additional_scripts, "C:/Users/umi"
        )
        joblist_arg += self._create_params_list_batch(post.joblist_late)
        for i in range(len(joblist_arg)):
            txt = f"set {name}[{i}]={joblist_arg[i]}"
            result += f"{txt}\n"
        return result

    def _create_config(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if template.iso_type == "windows":
            return self._create_config_batch(args, template)
        else:
            return self._create_config_bash(args, template)

    def _create_config_batch(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if args.addons.postinstall.create_config is False:
            return True
        interpath = self.files._get_path_intermediate(args)
        dstconf = f"{interpath}/umi/config"
        dstconffile = f"{dstconf}/env.bat"
        os.makedirs(dstconf, exist_ok=True)

        cfg_run = args.run.get_env_vars_batch()
        cfg_target = args.target.get_env_vars_batch()
        cfg_template = template.get_env_vars_batch()
        cfg_grub = args.addons.grub.get_env_vars_batch()
        cfg_ssh = args.addons.ssh.get_env_vars_batch()
        cfg_env = args.env.get_env_vars_batch()
        cfg_postinst = args.addons.postinstall.get_env_vars_batch()
        cfg_answerfile = args.addons.answerfile.get_env_vars_batch()
        if template.iso_type == "windows":
            cfg_joblist = self._create_params_alljobs_batch(args, "CFG_JOBS_ALL")
        else:
            cfg_joblist = self._create_params_alljobs_bash(args, "CFG_JOBS_ALL")
        arr = [
            "\n:: Template Config",
            *cfg_template,
            "\n:: Run Args",
            *cfg_run,
            "\n:: Target Args ",
            *cfg_target,
            "\n:: Grub Addon Args ",
            *cfg_grub,
            "\n:: SSH Addon Args ",
            *cfg_ssh,
            "\n:: Answerfile Addon Args ",
            *cfg_answerfile,
            "\n:: Postinstall Addon Args ",
            *cfg_postinst,
            "\n:: Postinstall Addon Joblist ",
            cfg_joblist,
            "\n:: Environment Args ",
            *cfg_env,
        ]

        contents = "\n".join(arr)
        if os.path.exists(dstconffile):
            self.files.rm(dstconffile)
        if self.files.append_to_file(dstconffile, contents) is False:
            return False
        return self.files.chmod(dstconffile, 777)

    def _create_config_bash(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if args.addons.postinstall.create_config is False:
            return True
        interpath = self.files._get_path_intermediate(args)
        dstconf = f"{interpath}/umi/config"
        dstconffile = f"{dstconf}/env.bash"
        os.makedirs(dstconf, exist_ok=True)

        cfg_run = args.run.get_env_vars_bash()
        cfg_target = args.target.get_env_vars_bash()
        cfg_template = template.get_env_vars_bash()
        cfg_grub = args.addons.grub.get_env_vars_bash()
        cfg_ssh = args.addons.ssh.get_env_vars_bash()
        cfg_env = args.env.get_env_vars_bash()
        cfg_postinst = args.addons.postinstall.get_env_vars_bash()
        cfg_answerfile = args.addons.answerfile.get_env_vars_bash()
        cfg_joblist = self._create_params_alljobs_bash(args, "CFG_JOBS_ALL")

        arr = [
            "#!/bin/bash",
            "\n# Template Config",
            *cfg_template,
            "\n# Run Args",
            *cfg_run,
            "\n# Target Args ",
            *cfg_target,
            "\n# Grub Addon Args ",
            *cfg_grub,
            "\n# SSH Addon Args ",
            *cfg_ssh,
            "\n# Answerfile Addon Args ",
            *cfg_answerfile,
            "\n# Postinstall Addon Args ",
            *cfg_postinst,
            "\n# Postinstall Addon Joblist ",
            cfg_joblist,
            "\n# Environment Args ",
            *cfg_env,
        ]

        contents = "\n".join(arr)
        if os.path.exists(dstconffile):
            self.files.rm(dstconffile)
        if self.files.append_to_file(dstconffile, contents) is False:
            return False
        return self.files.chmod(dstconffile, 777)

    # def _copy_bashrc(self, args: TaskConfig) -> bool:
    #     if args.addons.postinstall.bashrc_file == "":
    #         log_debug("Skipping File bashrc", "PostinstallAddon")
    #         return True
    #     srcfile = self.get_template_path_optional(
    #         "postinstall", args.addons.postinstall.bashrc_file, args
    #     )
    #     if os.path.exists(srcfile):
    #         log_debug(
    #             f"Copy File {args.addons.postinstall.bashrc_file}",
    #             "PostinstallAddon",
    #         )
    #         interpath = self.files._get_path_intermediate(args)
    #         dstconf = f"{interpath}/umi/config"
    #         dstconffile = f"{dstconf}/{args.addons.postinstall.bashrc_file}"
    #         os.makedirs(dstconf, exist_ok=True)
    #         return self.files.cp(srcfile, dstconffile)
    #     else:
    #         log_error(
    #             f"File not found: {args.addons.postinstall.bashrc_file}",
    #             "PostinstallAddon",
    #         )
    #     return False

    def _copy_bash_aliases(self, args: TaskConfig, template: TemplateConfig) -> bool:
        if template.iso_type == "windows":
            return True
        if args.addons.postinstall.bash_aliases == "":
            log_debug("Skipping File bash_aliases", "PostinstallAddon")
            return True
        srcfile = self.get_template_path_optional(
            "postinstall", args.addons.postinstall.bash_aliases, args
        )
        if os.path.exists(srcfile):
            log_debug(
                f"Copy File {args.addons.postinstall.bash_aliases}",
                "PostinstallAddon",
            )
            interpath = self.files._get_path_intermediate(args)
            dstconf = f"{interpath}/umi/config"
            dstconffile = f"{dstconf}/{args.addons.postinstall.bash_aliases}"
            os.makedirs(dstconf, exist_ok=True)
            return self.files.cp(srcfile, dstconffile)
        else:
            log_error(
                f"File not found: {args.addons.postinstall.bash_aliases}",
                "PostinstallAddon",
            )
        return False

    def _create_replacements_theme(
        self, args: TaskConfig, themefile: str
    ) -> list[Replaceable]:
        name = args.target.template
        hostname = args.addons.answerfile.host_name
        domain = args.addons.answerfile.host_domain
        ip = args.addons.answerfile.net_ip
        version = args.sys.tool_version
        dst = self.files._get_path_intermediate(args)
        kernel = self._extract_kernel_version(dst)
        rules = []
        if os.path.exists(themefile):
            rules += [
                Replaceable(themefile, "CFG_TYPE", name),
                Replaceable(themefile, "CFG_HOST", hostname),
                Replaceable(themefile, "CFG_DOMAIN", domain),
                Replaceable(themefile, "CFG_IP", ip),
                Replaceable(themefile, "CFG_KERNEL", kernel),
                Replaceable(themefile, "CFG_VERSION", version),
            ]
        return rules

    def _create_replacements_postinst(
        self, args: TaskConfig, postinst: str
    ) -> list[Replaceable]:
        c = args.addons.answerfile
        cfg_joblist = self._create_params_alljobs_bash(args)
        return [
            Replaceable(postinst, "CFG_JOBS_ALL", cfg_joblist),
            Replaceable(postinst, "CFG_USER_OTHER_NAME", c.user_other_name),
            Replaceable(postinst, "CFG_USER_OTHER_PW", c.user_other_pw),
        ]
