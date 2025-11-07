from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_info


class CloudInitAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "cloudinit")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        log_info("Nothing to do! Skipping...", self.__class__.__qualname__)
        return True
