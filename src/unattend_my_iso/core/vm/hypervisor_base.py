from abc import ABC, abstractmethod
from dataclasses import dataclass

from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.core.files.file_manager import UmiFileManager
from unattend_my_iso.core.generators.generator_cloudbase import (
    CIBaseConfig,
    UmiCloudBaseGenerator,
)


@dataclass
class HypervisorArgs:
    name: str
    vmtype: str
    uefi: bool
    cdrom: str
    disks: list[str]
    netdevs: list[list[str]]
    netbridges: list[list[str]]
    portfwd: list[list[int]]
    uplink_device: str
    sys_cpu: int
    sys_mem: int
    net_prepare_fw: bool
    net_prepare_nics: bool
    net_prepare_bridges: bool
    pidfile: str
    clean_old_vm: bool
    ci_config: CIBaseConfig


class UmiHypervisorBase(ABC):
    files: UmiFileManager = UmiFileManager()
    ci_gen: UmiCloudBaseGenerator = UmiCloudBaseGenerator()

    def __init__(self) -> None:
        pass

    @abstractmethod
    def vm_exec(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def vm_get_args(self, args: TaskConfig, template: TemplateConfig) -> HypervisorArgs:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def vm_run(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def vm_stop(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def vm_prepare_disks(self, args: TaskConfig, args_hv: HypervisorArgs):
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def vm_prepare_disk(self, args: TaskConfig, diskpath: str, size: str) -> bool:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def prepare_disk_efi(self, args: TaskConfig) -> bool:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def vm_prepare_tpm(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        raise NotImplementedError("Not implemented")
