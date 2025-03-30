import os
from dataclasses import dataclass, field
from typing import Any, Optional

# user
HOMEDIR = os.path.expanduser("~")
USER = os.getlogin()


@dataclass
class RunArgs:
    instname: str = "testvm"
    verbosity: int = 1
    diskname: str = "disk1.qcow2"
    disksize: int = 64
    uefi_boot: bool = True
    daemonize: bool = True
    uefi_ovmf_vars: str = "/usr/share/OVMF/OVMF_VARS.fd"
    uefi_ovmf_code: str = "/usr/share/OVMF/OVMF_CODE.fd"
    net_ports: list[tuple[int, int]] = field(default_factory=lambda: [(2222, 22)])
    net_devs: list[str] = field(default_factory=lambda: ["nat"])
    res_cpu: int = 4
    res_mem: int = 4096
    homedir: str = HOMEDIR
    user: str = USER


@dataclass
class AddonArgsAnswerFile:
    answerfile_enabled: bool = True
    locale_string: str = "en_US"
    locale_multi: str = "en_US.UTF-8"
    locale_keyboard: str = "de"
    host_name: str = "foo"
    host_domain: str = "cluster.local"
    net_dhcp: bool = False
    net_ip: str = "10.23.42.9"
    net_mask: str = "255.255.255.0"
    net_gateway: str = "10.23.42.1"
    net_dns: str = "10.23.42.1"
    disk_password: str = "diskpass"
    disk_cryptname: str = "vg_crypto"
    time_utc: bool = True
    time_zone: str = "EU/Berlin"
    time_ntp: bool = True
    user_root_enabled: bool = True
    user_root_password: str = "rootpass"
    user_other_enabled: bool = True
    user_other_name: str = "umi"
    user_other_fullname: str = "umi"
    user_other_password: str = "umipass"
    packages_install: list[str] = field(default_factory=lambda: [])
    grub_install_device: str = "default"


@dataclass
class AddonArgsSsh:
    ssh_enabled: bool = True
    keygen: bool = True
    config_client: str = "config"
    config_daemon: str = "sshd_config"
    config_auth: str = "authorized_keys"
    config_auth_append: str = f"{HOMEDIR}/.ssh/id_rsa.pub"
    config_key: str = "id_rsa"


@dataclass
class AddonArgsPostinstall:
    postinstall_enabled: bool = True
    enable_grub_theme: bool = True
    create_config: bool = True


@dataclass
class AddonArgsGrub:
    grub_enabled: bool = True
    grub_theme: str = "default"
    grub_icons: str = ""
    initrd_list: list[str] = field(
        default_factory=lambda: [
            "install.amd",
            # "install.amd/gtk",
            # "install",
            # "install/gtk",
        ]
    )
    sleeptime: int = 0
    timeout: int = -1


@dataclass
class AddonArgs:
    answerfile: AddonArgsAnswerFile
    ssh: AddonArgsSsh
    grub: AddonArgsGrub
    postinstall: AddonArgsPostinstall


@dataclass
class TargetArgs:
    file_prefix: str = "umi_"
    file_extension: str = "iso"
    file_mbr: str = "/usr/lib/ISOLINUX/isohdpfx.bin"
    template: str = "win11"
    proctype: str = "vmbuild_all"


def get_group_arguments(name: str) -> Optional[Any]:
    if name == "target":
        return TargetArgs()
    elif name == "run":
        return RunArgs()
    elif name == "addon_ssh":
        return AddonArgsSsh()
    elif name == "addon_grub":
        return AddonArgsGrub()
    elif name == "addon_postinstall":
        return AddonArgsPostinstall()
    elif name == "addon_answerfile":
        return AddonArgsAnswerFile()
    return None
