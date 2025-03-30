from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Optional
from unattend_my_iso.core.reader.cli_reader import CommandlineReader
from unattend_my_iso.common.args import (
    AddonArgs,
    AddonArgsAnswerFile,
    AddonArgsGrub,
    AddonArgsPostinstall,
    AddonArgsSsh,
    RunArgs,
    TargetArgs,
)
from unattend_my_iso.common.logging import log_debug, log_error, log_warn


# Globals
APP_VERSION = "0.0.1"
DEFAULT_TEMPLATE = "debian12"


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


def get_cli_group(name: str) -> Optional[Any]:
    reader = CommandlineReader()
    return reader.read_cli_group(name)


def get_default_group(name: str) -> Optional[Any]:
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


def _match_group(name: str, template_name: str) -> Optional[Any]:
    default_values = get_default_group(name)
    matched = _match_group_with_cli(default_values, name)
    return matched


def _match_group_with_cli(result: Optional[Any], target: str) -> Optional[Any]:
    if result is None or is_dataclass(result) is False:
        log_error(f"result is not a valid dataclass: {result}")
        return None
    cfg_cli = get_cli_group(target)
    if cfg_cli is None:
        log_error(f"client config is not a valid dataclass: {cfg_cli}")
        return None
    for field in fields(cfg_cli):
        name = field.name
        val = _get_normalized_value(result, cfg_cli, name)
        if val is not None:
            setattr(result, name, val)
            log_debug(f"cli_update   : group={target}, name={name}, value={val}")
    return result


def _get_normalized_value(obj_dest, obj_src, name: str) -> Optional[Any]:
    val = getattr(obj_src, name)
    if val is not None:
        if type(getattr(obj_dest, name)) is bool:
            lowername = str(val).lower()
            if lowername in ("true", "false"):
                val = True if lowername == "true" else False
    return val


def get_config(work_path: str) -> Optional[TaskConfig]:
    cfg_sys = get_cfg_sys(work_path)
    cli_target = get_cli_group("target")
    if cli_target is None:
        return None
    if isinstance(cli_target, TargetArgs) is False:
        template_name = DEFAULT_TEMPLATE
        log_warn(f"Template name not specified. Using default: {template_name}")
    else:
        template_name = cli_target.template
        log_debug(f"Use template : {template_name}")
    cfg_target = _match_group("target", template_name)
    if cfg_target is None or isinstance(cfg_target, TargetArgs) is False:
        log_error(f"Matched target config invalid: {cfg_target}")
        return None
    cfg_run = _match_group("run", template_name)
    if cfg_run is None or isinstance(cfg_run, RunArgs) is False:
        log_error(f"Matched run config invalid: {cfg_run}")
        return None
    cfg_ssh = _match_group("addon_ssh", template_name)
    if cfg_ssh is None or isinstance(cfg_ssh, AddonArgsSsh) is False:
        log_error(f"Matched addon_ssh config invalid: {cfg_ssh}")
        return None
    cfg_grub = _match_group("addon_grub", template_name)
    if cfg_grub is None or isinstance(cfg_grub, AddonArgsGrub) is False:
        log_error(f"Matched addon_grub config invalid: {cfg_grub}")
        return None
    cfg_post = _match_group("addon_postinstall", template_name)
    if cfg_post is None or isinstance(cfg_post, AddonArgsPostinstall) is False:
        log_error(f"Matched addon_postinstall config invalid: {cfg_post}")
        return None
    cfg_answer = _match_group("addon_answerfile", template_name)
    if cfg_answer is None or isinstance(cfg_answer, AddonArgsAnswerFile) is False:
        log_error(f"Matched addon_answerfile config invalid: {cfg_answer}")
        return None
    cfg_addons = AddonArgs(cfg_answer, cfg_ssh, cfg_grub, cfg_post)
    return TaskConfig(sys=cfg_sys, addons=cfg_addons, target=cfg_target, run=cfg_run)


def get_config_default(work_path: str) -> TaskConfig:
    cfg_sys = get_cfg_sys(work_path)
    args_answers = AddonArgsAnswerFile()
    args_ssh = AddonArgsSsh()
    args_grub = AddonArgsGrub()
    args_postinstall = AddonArgsPostinstall()
    cfg_addons = AddonArgs(args_answers, args_ssh, args_grub, args_postinstall)
    cfg_target = TargetArgs()
    cfg_run = RunArgs()
    return TaskConfig(sys=cfg_sys, addons=cfg_addons, target=cfg_target, run=cfg_run)
