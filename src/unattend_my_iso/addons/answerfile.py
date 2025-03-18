from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig


class AnswerFileAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "answerfile")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        templatepath = args.sys.template_path
        templatename = args.target.template
        interpath = args.sys.intermediate_path
        intername = args.target.template
        fullpreseed = f"{templatepath}/{templatename}/{template.preseed_file}"
        fullinter = f"{interpath}/{intername}"
        if self.files.cp(fullpreseed, fullinter):
            return True
        return False
