import os
from dataclasses import dataclass, field
from typing import Any, Optional

# user
HOMEDIR = os.path.expanduser("~")
USER = os.getlogin()
DEFAULT_SUBNET = "10.10.123"
DEFAULT_TIMEZONE = "EU/Berlin"
DEFAULT_LOCALE = "en_US"
DEFAULT_KEYBOARD = "de"
DEFAULT_PASSWORD_ROOT = "rootpass"
DEFAULT_PASSWORD_USER = "umipass"
DEFAULT_PASSWORD_CRYPTO = "diskpass"
DEFAULT_HOSTNAME = "foo"
DEFAULT_DOMAIN = "local"


class ArgumentBase:
    def get_config_values(self) -> dict[str, Any]:
        result = {}
        for el in vars(self):
            val = self.__dict__[el]
            result[f"CFG_{el.upper()}"] = val
        return result

    def get_env_vars(self) -> list[str]:
        result = []
        values = self.get_config_values()
        for key, val in values.items():
            if isinstance(val, dict):
                normlist = self.normalize_dict(val)
                for normentry in normlist:
                    result.append(normentry)
            else:
                normval = self.normalize_value(val)
                result.append(f"{key}={normval}")
        return result

    def normalize_value(self, val: Any) -> str:
        if isinstance(val, bool):
            return "1" if val is True else "0"
        elif isinstance(val, str):
            return f'"{val}"'
        elif isinstance(val, int):
            return str(val)
        elif isinstance(val, tuple):
            return f'"{val[0]},{val[1]}"'
        elif isinstance(val, list):
            result = ["("]
            for listval in val:
                if isinstance(listval, list):
                    strlist = str(listval).removeprefix("[").removesuffix("]")
                    normval = f'"{strlist}"'
                else:
                    normval = self.normalize_value(listval)
                result.append(normval)
            result += [")"]
            return " ".join(result)
        else:
            return str(val)

    def normalize_dict(self, val: Any) -> list[str]:
        if isinstance(val, dict):
            result = []
            for key, innerval in val.items():
                normval = self.normalize_value(innerval)
                result.append(f"{key}={normval}")
            return result
        else:
            return []


@dataclass
class EnvironmentArgs(ArgumentBase):
    env_args: dict[str, Any] = field(default_factory=lambda: {})


@dataclass
class RunArgs(ArgumentBase):
    vmname: str = "testvm"
    verbosity: int = 1
    disks: list[list[str]] = field(
        default_factory=lambda: [["disk1.qcow2", "64G", "hdd"]]
    )
    uefi_boot: bool = True
    cdrom_boot: bool = True
    daemonize: bool = True
    uefi_ovmf_vars: str = "/usr/share/OVMF/OVMF_VARS.fd"
    uefi_ovmf_code: str = "/usr/share/OVMF/OVMF_CODE.fd"
    uplink_dev: str = ""
    net_ports: list[list[int]] = field(default_factory=lambda: [[]])
    net_devs: list[list[str]] = field(default_factory=lambda: [[]])
    net_bridges: list[list[str]] = field(
        default_factory=lambda: [["vmbr0", "10.10.123.1", "24", True]]
    )
    res_cpu: int = 2
    res_mem: int = 2048
    net_prepare_fw: bool = True
    net_prepare_nics: bool = True
    net_prepare_bridges: bool = True
    clean_old_vm: bool = False
    build_homedir: str = HOMEDIR
    build_user: str = USER
    file_pid: str = "vm.pid"


@dataclass
class AddonArgsAnswerFile(ArgumentBase):
    answerfile_enabled: bool = True
    locale_string: str = DEFAULT_LOCALE
    locale_multi: str = f"{DEFAULT_LOCALE}.UTF-8"
    locale_keyboard: str = DEFAULT_KEYBOARD
    host_name: str = DEFAULT_HOSTNAME
    host_domain: str = DEFAULT_DOMAIN
    net_dhcp: bool = False
    net_ip: str = f"{DEFAULT_SUBNET}.111"
    net_mask: str = "255.255.255.0"
    net_gateway: str = f"{DEFAULT_SUBNET}.1"
    net_dns: str = f"{DEFAULT_SUBNET}.1"
    disk_password: str = DEFAULT_PASSWORD_CRYPTO
    disk_cryptname: str = "vg_crypto"
    time_utc: bool = True
    time_zone: str = DEFAULT_TIMEZONE
    time_ntp: bool = True
    user_root_enabled: bool = True
    user_root_password: str = DEFAULT_PASSWORD_ROOT
    user_other_enabled: bool = True
    user_other_name: str = "umi"
    user_other_fullname: str = "umi"
    user_other_password: str = DEFAULT_PASSWORD_USER
    packages_install: list[str] = field(default_factory=lambda: [])
    grub_install_device: str = "default"
    include_offline_packages: list[str] = field(default_factory=lambda: [])


@dataclass
class AddonArgsSsh(ArgumentBase):
    ssh_enabled: bool = True
    keygen: bool = True
    config_client: str = ""
    config_daemon: str = "sshd_config"
    config_auth: str = "authorized_keys"
    config_auth_append: str = f"{HOMEDIR}/.ssh/id_rsa.pub"
    config_key: str = "id_rsa"


@dataclass
class AddonArgsPostinstall(ArgumentBase):
    postinstall_enabled: bool = True
    enable_grub_theme: bool = True
    create_config: bool = True
    bashrc_file: str = ".bashrc"
    joblist_early: list[str] = field(default_factory=lambda: [])
    joblist_late: list[str] = field(default_factory=lambda: [])
    copy_additional_scripts: list[str] = field(default_factory=lambda: [])


@dataclass
class AddonArgsGrub(ArgumentBase):
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
    grub_kernel_lvm_alt1: str = "6.2.16-20-pve"
    grub_kernel_lvm_alt2: str = "6.8.12-9-pve"
    sleeptime: int = 0
    timeout: int = -1


@dataclass
class AddonArgs:
    answerfile: AddonArgsAnswerFile
    ssh: AddonArgsSsh
    grub: AddonArgsGrub
    postinstall: AddonArgsPostinstall

    def get_env_vars(self) -> list[str]:
        result = [
            *(self.answerfile.get_env_vars()),
            *(self.ssh.get_env_vars()),
            *(self.grub.get_env_vars()),
            *(self.postinstall.get_env_vars()),
        ]
        return result


@dataclass
class TargetArgs(ArgumentBase):
    file_prefix: str = "umi_"
    file_extension: str = "iso"
    file_mbr: str = "/usr/lib/ISOLINUX/isohdpfx.bin"
    template: str = "win11"
    template_overlay: str = ""
    proctype: str = "build_all"


def get_group_arguments(name: str) -> Optional[Any]:
    if name == "target":
        return TargetArgs()
    elif name == "env":
        return EnvironmentArgs()
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
