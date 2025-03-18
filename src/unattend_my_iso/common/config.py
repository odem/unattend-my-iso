from dataclasses import dataclass
from unattend_my_iso.common.args import AddonArgs, RunArgs, TargetArgs

# Defaults Run
DEFAULT_RUN_CPU = 4
DEFAULT_RUN_MEMORY = 4096
DEFAULT_RUN_DISK0_NAME = "disk1.qcow2"
DEFAULT_RUN_DISK0_SIZE = 64
DEFAULT_RUN_PORTS = [(2222, 22)]
DEFAULT_RUN_NETDEVS = ["nat"]
DEFAULT_RUN_UEFI_BOOT = True
DEFAULT_RUN_OVMF_CODE = "/usr/share/OVMF/OVMF_CODE.fd"
DEFAULT_RUN_OVMF_VARS = "/usr/share/OVMF/OVMF_VARS.fd"

# Defaults Target
DEFAULT_TARGET_MBRFILE = "/usr/lib/ISOLINUX/isohdpfx.bin"
DEFAULT_TARGET_ISO_EXT = "iso"
DEFAULT_TARGET_ISO_PREFIX = "umi_"

# Default Addons
DEFAULT_ADDON_ANSWER = True
DEFAULT_ADDON_GRUB = True
DEFAULT_ADDON_SSH = True
DEFAULT_ADDON_POSTINST = True


@dataclass
class SysConfig:
    template_path: str
    mnt_path: str
    intermediate_path: str
    iso_path: str
    vm_path: str


@dataclass
class TaskConfig:
    sys: SysConfig
    addons: AddonArgs
    target: TargetArgs
    run: RunArgs


@dataclass
class TemplateConfig:
    name: str
    iso_name: str
    iso_url: str
    preseed_file: str
    path_ssh: str
    path_grub: str
    path_postinstall: str


def get_cfg_sys(work_path: str) -> SysConfig:
    return SysConfig(
        template_path=f"{work_path}/templates",
        mnt_path=f"{work_path}/data/mounts",
        intermediate_path=f"{work_path}/data/out",
        iso_path=f"{work_path}/data/iso",
        vm_path=f"{work_path}/data/vm",
    )


def get_cfg_task(work_path: str) -> TaskConfig:
    cfg_sys = get_cfg_sys(work_path)
    cfg_addons = AddonArgs(
        addon_answerfile=DEFAULT_ADDON_ANSWER,
        addon_ssh=DEFAULT_ADDON_SSH,
        addon_grubmenu=DEFAULT_ADDON_GRUB,
        addon_postinstall=DEFAULT_ADDON_POSTINST,
    )
    cfg_target = TargetArgs(
        template="debian12",
        file_prefix=DEFAULT_TARGET_ISO_PREFIX,
        file_extension=DEFAULT_TARGET_ISO_EXT,
        mbrfile=DEFAULT_TARGET_MBRFILE,
    )
    cfg_run = RunArgs(
        DEFAULT_RUN_DISK0_NAME,
        DEFAULT_RUN_DISK0_SIZE,
        DEFAULT_RUN_UEFI_BOOT,
        DEFAULT_RUN_OVMF_VARS,
        DEFAULT_RUN_OVMF_CODE,
        DEFAULT_RUN_PORTS,
        DEFAULT_RUN_NETDEVS,
        DEFAULT_RUN_CPU,
        DEFAULT_RUN_MEMORY,
    )
    return TaskConfig(sys=cfg_sys, addons=cfg_addons, target=cfg_target, run=cfg_run)
