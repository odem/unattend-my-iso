from abc import ABC, abstractmethod

from unattend_my_iso.core.files.file_manager import UmiFileManager
from unattend_my_iso.common.config import TaskConfig, TemplateConfig


class UmiAddon(ABC):

    addon_name: str

    def __init__(self, name: str):
        self.addon_name = name
        self.files = UmiFileManager()

    @abstractmethod
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        raise NotImplementedError("Not implemented")
