from dataclasses import dataclass, field
from typing import Any
from unattend_my_iso.common.args import (
    AddonArgs,
    AddonArgsAnswerFile,
    AddonArgsGrub,
    AddonArgsPostinstall,
    AddonArgsSsh,
    ArgumentBase,
    EnvironmentArgs,
    RunArgs,
    TargetArgs,
)
from unattend_my_iso.common.const import APP_VERSION


@dataclass
class SysConfig:
    path_templates: str
    path_mnt: str
    path_intermediate: str
    path_iso: str
    path_vm: str
    path_cwd: str
    tool_version: str


@dataclass
class TaskConfig:
    sys: SysConfig
    addons: AddonArgs
    target: TargetArgs
    run: RunArgs
    env: EnvironmentArgs


@dataclass
class TaskResult:
    success: bool
    msg: str
    msg_short: str
    msg_out: str
    msg_err: str


@dataclass
class TemplateConfig(ArgumentBase):
    name: str
    name_overlay: str
    iso_name: str
    iso_url: str
    iso_type: str
    virtio_name: str = ""
    virtio_url: str = ""
    answerfile: str = ""
    path_postinstall: str = ""
    file_postinstall: str = ""
    files_overlay: list[str] = field(default_factory=lambda: [])
    optional_params: dict[str, Any] = field(default_factory=lambda: {})


def get_cfg_sys(work_path: str) -> SysConfig:
    return SysConfig(
        path_templates=f"{work_path}/templates",
        path_mnt=f"{work_path}/data/mounts",
        path_intermediate=f"{work_path}/data/out",
        path_iso=f"{work_path}/data/iso",
        path_vm=f"{work_path}/data/vm",
        path_cwd=work_path,
        tool_version=APP_VERSION,
    )


def get_config_default(work_path: str) -> TaskConfig:
    cfg_sys = get_cfg_sys(work_path)
    args_answers = AddonArgsAnswerFile()
    args_ssh = AddonArgsSsh()
    args_grub = AddonArgsGrub()
    args_postinstall = AddonArgsPostinstall()
    cfg_addons = AddonArgs(args_answers, args_ssh, args_grub, args_postinstall)
    cfg_target = TargetArgs()
    cfg_run = RunArgs()
    cfg_env = EnvironmentArgs()
    return TaskConfig(
        sys=cfg_sys, addons=cfg_addons, target=cfg_target, run=cfg_run, env=cfg_env
    )
