from dataclasses import dataclass
from pathlib import Path
import tomllib
import os
from typing import Optional
from unattend_my_iso.helpers.logging import log_error


@dataclass
class SysConfig:
    template_path: str
    mnt_path: str
    intermediate_path: str
    iso_path: str
    vm_path: str


@dataclass
class AddonConfig:
    addon_ssh: bool
    addon_grubmenu: bool
    addon_postinstall: bool


@dataclass
class TargetConfig:
    template: str


@dataclass
class TaskConfig:
    sys: SysConfig
    addons: AddonConfig
    target: TargetConfig


@dataclass
class TaskResult:
    success: bool
    msg: str
    msg_short: str
    msg_out: str
    msg_err: str


@dataclass
class IsoTemplate:
    name: str
    iso_name: str
    iso_url: str
    preseed_file: str
    path_ssh: str
    path_grub: str
    path_postinstall: str


def read_templates_isos(parent_folder: str) -> dict[str, IsoTemplate]:
    result = {}
    for entry in os.scandir(parent_folder):
        if entry.is_dir():
            dir = Path(entry.path).resolve()
            full = f"{dir}/desc.toml"
            config_template = read_template_iso(full)
            if config_template is not None:
                result[config_template.name] = config_template
    return result


def read_template_iso(file: str) -> Optional[IsoTemplate]:
    if os.path.exists(file):
        with open(file, "rb") as f:
            toml_data = tomllib.load(f)
            return IsoTemplate(**toml_data["description"])
    else:
        log_error("Template config is not a valid file")
    return None


def create_default_config(work_path: str):
    cfg_sys = SysConfig(
        template_path=f"{work_path}/templates",
        mnt_path=f"{work_path}/data/mounts",
        intermediate_path=f"{work_path}/data/out",
        iso_path=f"{work_path}/data/iso",
        vm_path=f"{work_path}/data/vm",
    )
    cfg_addons = AddonConfig(
        addon_ssh=True, addon_grubmenu=True, addon_postinstall=True
    )
    cfg_target = TargetConfig(template="debian12")
    return TaskConfig(sys=cfg_sys, addons=cfg_addons, target=cfg_target)
