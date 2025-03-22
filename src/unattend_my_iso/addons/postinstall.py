from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
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
        src = f"{templatepath}/{templatename}"
        dst = f"{interpath}/{intername}/umi/postinstall"
        postfolder = f"{src}/{template.path_postinstall}"
        if self.files.cp(postfolder, dst) is False:
            return False
        return self._apply_replacements(args, f"{dst}/postinstall.bat")

    def _apply_replacements(self, args: TaskConfig, postinst: str) -> bool:
        c = args.addons.answerfile
        rules = [Replaceable(postinst, "CFG_USER_OTHER_NAME", c.user_other_name)]
        for rule in rules:
            self.replacements.append(rule)
        return self.do_replacements()
