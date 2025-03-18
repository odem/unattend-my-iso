from abc import ABC, abstractmethod

from unattend_my_iso.core.files.file_manager import UmiFileManager
from unattend_my_iso.helpers.config import IsoTemplate, TaskConfig
from unattend_my_iso.helpers.logging import log_info


class UmiAddon(ABC):

    addon_name: str

    def __init__(self, name: str):
        self.addon_name = name
        self.files = UmiFileManager()

    @abstractmethod
    def integrate_addon(self, args: TaskConfig, template: IsoTemplate) -> bool:
        raise NotImplementedError("Not implemented")
