import os
from typing_extensions import override
from unattend_my_iso.addons.addon_base import UmiAddon
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error


class LiveBootAddon(UmiAddon):
    def __init__(self):
        UmiAddon.__init__(self, "live")

    @override
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        return True
