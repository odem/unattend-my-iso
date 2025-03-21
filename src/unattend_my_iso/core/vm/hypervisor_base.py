from abc import ABC, abstractmethod
from dataclasses import dataclass

from unattend_my_iso.common.config import TaskConfig
from unattend_my_iso.core.files.file_manager import UmiFileManager


@dataclass
class HypervisorArgs:
    name: str
    uefi: bool
    cdrom: str
    disks: list[str]
    netdevs: list[str]
    portfwd: list[tuple[int, int]]
    sys_cpu: int
    sys_mem: int


class UmiHypervisorBase(ABC):
    files: UmiFileManager = UmiFileManager()

    def __init__(self) -> None:
        pass

    @abstractmethod
    def vm_get_args(self, args: TaskConfig) -> HypervisorArgs:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def vm_run(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def vm_prepare_disks(self, args: TaskConfig, args_hv: HypervisorArgs):
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def vm_prepare_disk(self, args: TaskConfig, diskpath: str) -> bool:
        raise NotImplementedError("Not implemented")
