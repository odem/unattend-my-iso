from dataclasses import dataclass
from unattend_my_iso.common.args import (
    AddonArgs,
    AddonArgsAnswerFile,
    AddonArgsGrub,
    AddonArgsPostinstall,
    AddonArgsSsh,
    RunArgs,
    TargetArgs,
)

# Globals
APP_VERSION = "0.0.1"

# Defaults Run
DEFAULT_RUN_CPU = 8
DEFAULT_RUN_MEMORY = 32000
DEFAULT_RUN_DISK0_NAME = "disk1.qcow2"
DEFAULT_RUN_DISK0_SIZE = 64
DEFAULT_RUN_PORTS = [(2222, 22)]
DEFAULT_RUN_NETDEVS = ["nat"]
DEFAULT_RUN_UEFI_BOOT = True
DEFAULT_RUN_OVMF_CODE = "/usr/share/OVMF/OVMF_CODE.fd"
DEFAULT_RUN_OVMF_VARS = "/usr/share/OVMF/OVMF_VARS.fd"

# Defaults target
DEFAULT_TARGET_MBRFILE = "/usr/lib/ISOLINUX/isohdpfx.bin"
DEFAULT_TARGET_ISO_EXT = "iso"
DEFAULT_TARGET_ISO_PREFIX = "umi_"

# Defaults Ssh
DEFAULT_ADDON_SSH_ENABLED = True

# Defaults postinstall
DEFAULT_ADDON_POSTINST_ENABLED = True

# Defaults Grubs
DEFAULT_ADDON_GRUB_ENABLED = True
DEFAULT_ADDON_GRUB_ICONS = ""
DEFAULT_ADDON_GRUB_THEME = "Cyberpunk"
DEFAULT_ADDON_GRUB_TIMEOUT = -1
DEFAULT_ADDON_GRUB_SLEEPTIME = 1
DEFAULT_ADDON_GRUB_INITRD_LIST = [
    "install.amd",
    "install.amd/gtk",
    "install",
    "install/gtk",
]

# Defaults answerfile
DEFAULT_ADDON_ANSWER_ENABLED = True
DEFAULT_ADDON_ANSWER_LOCALE_STRING = "en_US"
DEFAULT_ADDON_ANSWER_LOCALE_MULTI = "en_US.UTF-8"
DEFAULT_ADDON_ANSWER_LOCALE_KEYBOARD = "de"
DEFAULT_ADDON_ANSWER_HOST_NAME = "foo"
DEFAULT_ADDON_ANSWER_HOST_DOMAIN = "local"
DEFAULT_ADDON_ANSWER_NET_DHCP = False
DEFAULT_ADDON_ANSWER_NET_IP = "10.23.42.9"
DEFAULT_ADDON_ANSWER_NET_MASK = "255.255.255.0"
DEFAULT_ADDON_ANSWER_NET_GATEWAY = "10.23.42.1"
DEFAULT_ADDON_ANSWER_NET_DNS = "10.23.42.1"
DEFAULT_ADDON_ANSWER_TIME_UTC = True
DEFAULT_ADDON_ANSWER_TIME_ZONE = "EU/Berlin"
DEFAULT_ADDON_ANSWER_TIME_NTP = True
DEFAULT_ADDON_ANSWER_USER_ROOT_ENABLED = True
DEFAULT_ADDON_ANSWER_USER_ROOT_PASSWORD = "rootpass"
DEFAULT_ADDON_ANSWER_USER_OTHER_ENABLED = False
DEFAULT_ADDON_ANSWER_USER_OTHER_NAME = "umi"
DEFAULT_ADDON_ANSWER_USER_OTHER_FULLNAME = "umi"
DEFAULT_ADDON_ANSWER_USER_OTHER_PASSWORD = "umipass"
DEFAULT_ADDON_ANSWER_PACKAGES_INSTALL = [
    "openssh-server",
    "build-essential",
    "vim",
    "git",
    "make",
    "debconf",
    "sudo",
    "lsb-release",
    "net-tools",
    "psmisc",
    "dnsutils",
    "keyboard-configuration",
    "console-setup",
    "fontconfig",
    "otf2bdf",
    "bdf2psf",
    "fontforge",
]
DEFAULT_ADDON_ANSWER_GRUB_INSTALL_DEVICE = "/dev/vda"


@dataclass
class SysConfig:
    template_path: str
    mnt_path: str
    intermediate_path: str
    iso_path: str
    vm_path: str
    tool_version: str


@dataclass
class TaskConfig:
    sys: SysConfig
    addons: AddonArgs
    target: TargetArgs
    run: RunArgs


@dataclass
class TemplateConfig:
    name: str
    virtio_name: str
    virtio_url: str
    iso_name: str
    iso_url: str
    iso_type: str
    answerfile: str
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
        tool_version=APP_VERSION,
    )


def get_cfg_task(work_path: str) -> TaskConfig:
    cfg_sys = get_cfg_sys(work_path)
    args_answers = AddonArgsAnswerFile(
        DEFAULT_ADDON_ANSWER_ENABLED,
        DEFAULT_ADDON_ANSWER_LOCALE_STRING,
        DEFAULT_ADDON_ANSWER_LOCALE_MULTI,
        DEFAULT_ADDON_ANSWER_LOCALE_KEYBOARD,
        DEFAULT_ADDON_ANSWER_HOST_NAME,
        DEFAULT_ADDON_ANSWER_HOST_DOMAIN,
        DEFAULT_ADDON_ANSWER_NET_DHCP,
        DEFAULT_ADDON_ANSWER_NET_IP,
        DEFAULT_ADDON_ANSWER_NET_MASK,
        DEFAULT_ADDON_ANSWER_NET_GATEWAY,
        DEFAULT_ADDON_ANSWER_NET_DNS,
        DEFAULT_ADDON_ANSWER_TIME_UTC,
        DEFAULT_ADDON_ANSWER_TIME_ZONE,
        DEFAULT_ADDON_ANSWER_TIME_NTP,
        DEFAULT_ADDON_ANSWER_USER_ROOT_ENABLED,
        DEFAULT_ADDON_ANSWER_USER_ROOT_PASSWORD,
        DEFAULT_ADDON_ANSWER_USER_OTHER_ENABLED,
        DEFAULT_ADDON_ANSWER_USER_OTHER_NAME,
        DEFAULT_ADDON_ANSWER_USER_OTHER_FULLNAME,
        DEFAULT_ADDON_ANSWER_USER_OTHER_PASSWORD,
        DEFAULT_ADDON_ANSWER_PACKAGES_INSTALL,
        DEFAULT_ADDON_ANSWER_GRUB_INSTALL_DEVICE,
    )

    args_ssh = AddonArgsSsh(DEFAULT_ADDON_SSH_ENABLED)
    args_grub = AddonArgsGrub(
        DEFAULT_ADDON_GRUB_ENABLED,
        DEFAULT_ADDON_GRUB_THEME,
        DEFAULT_ADDON_GRUB_ICONS,
        DEFAULT_ADDON_GRUB_INITRD_LIST,
        DEFAULT_ADDON_GRUB_SLEEPTIME,
        DEFAULT_ADDON_GRUB_TIMEOUT,
    )
    args_postinstall = AddonArgsPostinstall(DEFAULT_ADDON_POSTINST_ENABLED)
    cfg_addons = AddonArgs(
        answerfile=args_answers,
        ssh=args_ssh,
        grub=args_grub,
        postinstall=args_postinstall,
    )
    cfg_target = TargetArgs(
        template="win11",
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
