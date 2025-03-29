from dataclasses import dataclass


@dataclass
class RunArgs:
    diskname: str
    disksize: int
    uefi: bool
    daemonize: bool
    uefi_ovmf_vars: str
    uefi_ovmf_code: str
    net_ports: list[tuple[int, int]]
    net_devs: list[str]
    res_cpu: int
    res_mem: int


@dataclass
class AddonArgsAnswerFile:
    enabled: bool
    locale_string: str
    locale_multi: str
    locale_keyboard: str
    host_name: str
    host_domain: str
    net_dhcp: bool
    net_ip: str
    net_mask: str
    net_gateway: str
    net_dns: str
    disk_password: str
    disk_cryptname: str
    time_utc: bool
    time_zone: str
    time_ntp: bool
    user_root_enabled: bool
    user_root_password: str
    user_other_enabled: bool
    user_other_name: str
    user_other_fullname: str
    user_other_password: str
    packages_install: list[str]
    grub_install_device: str


@dataclass
class AddonArgsSsh:
    enabled: bool
    keygen: bool
    config_client: str
    config_daemon: str
    config_auth: str
    config_auth_append: str
    config_key: str


@dataclass
class AddonArgsPostinstall:
    enabled: bool
    enable_grub_theme: bool
    create_config: bool


@dataclass
class AddonArgsGrub:
    enabled: bool
    grub_theme: str
    grub_icons: str
    initrd_list: list[str]
    sleeptime: int
    timeout: int


@dataclass
class AddonArgs:
    answerfile: AddonArgsAnswerFile
    ssh: AddonArgsSsh
    grub: AddonArgsGrub
    postinstall: AddonArgsPostinstall


@dataclass
class TargetArgs:
    file_prefix: str
    file_extension: str
    mbrfile: str
    template: str
