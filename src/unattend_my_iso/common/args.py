from dataclasses import dataclass


@dataclass
class RunArgs:
    diskname: str
    disksize: int
    uefi: bool
    uefi_ovmf_vars: str
    uefi_ovmf_code: str
    net_ports: list[tuple[int, int]]
    net_devs: list[str]
    res_cpu: int
    res_mem: int


@dataclass
class AddonArgs:
    addon_answerfile: bool
    addon_ssh: bool
    addon_grubmenu: bool
    addon_postinstall: bool


@dataclass
class TargetArgs:
    file_prefix: str
    file_extension: str
    mbrfile: str
    template: str
