from dataclasses import dataclass, field
from typing import Any, Optional
from unattend_my_iso.common.const import (
    DEFAULT_DOMAIN,
    DEFAULT_HOSTNAME,
    DEFAULT_KEYBOARD,
    DEFAULT_LOCALE,
    DEFAULT_PASSWORD_CHARSET,
    DEFAULT_PASSWORD_CRYPTO,
    DEFAULT_PASSWORD_LENGTH,
    DEFAULT_PASSWORD_ROOT,
    DEFAULT_PASSWORD_USER,
    DEFAULT_SUBNET,
    DEFAULT_TIMEZONE,
    DEFAULT_USERNAME,
    DEFAULT_VGNAME,
    HOME,
    USER,
)


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
        default_factory=lambda: [["disk1.qcow2", "256G", "hdd"]]
    )
    uefi_boot: bool = True
    cdrom_boot: bool = True
    daemonize: bool = True
    uefi_ovmf_vars: str = "/usr/share/OVMF/OVMF_VARS.fd"
    uefi_ovmf_code: str = "/usr/share/OVMF/OVMF_CODE.fd"
    uplink_dev: str = ""
    net_ports: list[list[int]] = field(default_factory=lambda: [[]])
    net_devs: list[list[str]] = field(default_factory=lambda: [["nat"]])
    net_bridges: list[list[str]] = field(default_factory=lambda: [[]])
    res_cpu: int = 2
    res_mem: int = 2048
    net_prepare_fw: bool = True
    net_prepare_nics: bool = True
    net_prepare_bridges: bool = True
    clean_old_vm: bool = False
    build_homedir: str = HOME
    build_user: str = USER
    file_pid: str = "vm.pid"


@dataclass
class AddonArgsAnswerFile(ArgumentBase):
    answerfile_enabled: bool = True
    answerfile_enable_networking: bool = True
    answerfile_enable_dhcp: bool = True
    answerfile_enable_crypto: bool = False
    answerfile_enable_lvm: bool = False
    answerfile_confirm_partitioning: bool = True
    answerfile_confirm_final_reboot: bool = True
    answerfile_hook_dir_cdrom: str = "/umi"
    answerfile_hook_dir_target: str = "/opt/umi"
    answerfile_hook_filename: str = "postinstall/postinstall.bash"
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
    disk_lvm_vg: str = DEFAULT_VGNAME
    time_utc: bool = True
    time_zone: str = DEFAULT_TIMEZONE
    time_ntp: bool = True
    user_root_enabled: bool = True
    user_root_pw: str = DEFAULT_PASSWORD_ROOT
    user_other_enabled: bool = True
    user_other_name: str = DEFAULT_USERNAME
    user_other_fullname: str = DEFAULT_USERNAME
    user_other_pw: str = DEFAULT_PASSWORD_USER
    additional_users: list[str] = field(default_factory=lambda: [])
    sudo_users: list[str] = field(default_factory=lambda: [])
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
    config_auth_append: str = f"{HOME}/.ssh/id_rsa.pub"
    config_key: str = "id_rsa"


@dataclass
class AddonArgsPostinstall(ArgumentBase):
    postinstall_enabled: bool = True
    enable_grub_theme: bool = True
    create_config: bool = True
    bashrc_file: str = ".bashrc"
    password_length: int = DEFAULT_PASSWORD_LENGTH
    password_charset: str = DEFAULT_PASSWORD_CHARSET
    joblist_early: list[str] = field(default_factory=lambda: [])
    joblist_late: list[str] = field(default_factory=lambda: [])
    copy_additional_scripts: list[str] = field(default_factory=lambda: [])
    exec_additional_scripts: list[str] = field(default_factory=lambda: [])


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
    grub_kernel_lvm_alt1: str = ""
    grub_kernel_lvm_alt2: str = ""
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
    work_path: str = ""


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
