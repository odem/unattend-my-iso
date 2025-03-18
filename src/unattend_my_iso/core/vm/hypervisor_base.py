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
    def get_hv_args(self, args: TaskConfig) -> HypervisorArgs:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def run_vm(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def prepare_disk_vm(self, args: TaskConfig, diskpath: str, size_gb: int) -> bool:
        raise NotImplementedError("Not implemented")
