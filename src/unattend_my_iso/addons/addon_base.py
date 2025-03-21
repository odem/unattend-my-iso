from abc import ABC, abstractmethod
from unattend_my_iso.common.model import Replaceable
from unattend_my_iso.core.files.file_manager import UmiFileManager
from unattend_my_iso.common.config import TaskConfig, TemplateConfig


class UmiAddon(ABC):

    addon_name: str
    replacements: list[Replaceable]

    def __init__(self, name: str):
        self.addon_name = name
        self.files = UmiFileManager()
        self.replacements = []

    def do_replacements(self) -> bool:
        for rule in self.replacements:
            self.files.replace_string(rule.filename, rule.searchterm, rule.replacement)
        return True

    @abstractmethod
    def integrate_addon(self, args: TaskConfig, template: TemplateConfig) -> bool:
        raise NotImplementedError("Not implemented")
