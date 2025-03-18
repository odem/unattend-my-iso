from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.helpers.config import IsoTemplate, TaskConfig
from unattend_my_iso.helpers.logging import log_debug


class PostinstallAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "postinstall")

    @override
    def integrate_addon(self, args: TaskConfig, template: IsoTemplate) -> bool:
        templatepath = args.sys.template_path
        templatename = args.target.template
        interpath = args.sys.intermediate_path
        intername = args.target.template
        src = f"{templatepath}/{templatename}"
        dst = f"{interpath}/{intername}/umi"
        postfolder = f"{src}/{template.path_postinstall}"
        if self.files.copy_folder(postfolder, dst) is False:
            return False
        log_debug(f"Integrated    : {self.addon_name}")
        return True
