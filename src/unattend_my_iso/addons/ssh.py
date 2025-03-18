from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig


class SshAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "ssh")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        templatepath = args.sys.template_path
        templatename = args.target.template
        interpath = args.sys.intermediate_path
        intername = args.target.template
        src = f"{templatepath}/{templatename}"
        dst = f"{interpath}/{intername}/umi/ssh"
        if self.files.cp(f"{src}/{template.path_ssh}", dst) is False:
            return False
        return True
