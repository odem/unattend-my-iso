from dataclasses import fields, is_dataclass
import os
import sys
from typing import Any, Optional
from unattend_my_iso.common.config import SysConfig, TaskConfig, get_cfg_sys
from unattend_my_iso.common.const import (
    DEFAULT_TEMPLATE,
    DEFAULT_TEMPLATE_OVERLAY,
    GLOBAL_WORKPATHS,
)
from unattend_my_iso.common.logging import log_debug, log_error, log_info
from unattend_my_iso.common.templates import list_overlays
from unattend_my_iso.common.args import (
    AddonArgs,
    AddonArgsAnswerFile,
    AddonArgsGrub,
    AddonArgsPostinstall,
    AddonArgsSsh,
    EnvironmentArgs,
    RunArgs,
    TargetArgs,
    get_group_arguments,
)


def get_cli_group(name: str) -> Optional[Any]:
    from unattend_my_iso.core.reader.reader_cli import CommandlineReader

    reader = CommandlineReader()
    return reader.read_cli_group(name)


def _match_group(
    name: str, template_name: str, template_path: str, overlay_name: str
) -> Optional[Any]:
    cfg_default = get_group_arguments(name)
    cfg_template = _match_group_with_template(
        cfg_default, name, template_name, template_path
    )
    if overlay_name != "":
        cfg_template = _match_group_with_template(
            cfg_default, name, template_name, template_path, overlay_name
        )
    cfg_cli = _match_group_with_cli(cfg_template, name)
    return cfg_cli


def _match_group_with_template(
    result: Optional[Any],
    target: str,
    template_name: str,
    template_path: str,
    overlay_name: str = "",
) -> Optional[Any]:
    from unattend_my_iso.common.templates import read_template_group

    if result is None or is_dataclass(result) is False:
        log_error(f"result is not a valid dataclass: {result}", "ConfigReader")
        return None
    filename = "desc.toml"
    if overlay_name != "":
        filename = f"desc.{overlay_name}.toml"
    file_template = f"{template_path}/iso/{template_name}/{filename}"
    toml_group: list | dict = read_template_group(file_template, target)
    if isinstance(toml_group, list) and len(toml_group) == 1:
        cfg_dict = toml_group[0]
        if isinstance(cfg_dict, dict) and isinstance(result, EnvironmentArgs):
            for dkey, dval in cfg_dict.items():
                result.env_args[dkey] = dval
                log_debug(f"env_update for {target} name={dkey}", "ConfigReader")
        return result
    else:
        for fld in toml_group.items():
            name = fld[0]
            val = fld[1]
            setattr(result, name, val)
            log_debug(f"tpl_update for {target} name={name} val={val}", "ConfigReader")
        return result


def _match_group_with_cli(result: Optional[Any], target: str) -> Optional[Any]:
    if result is None or is_dataclass(result) is False:
        log_error(f"result is not a valid dataclass: {result}", "ConfigReader")
        return None
    cfg_cli = get_cli_group(target)
    if cfg_cli is None:
        log_error(f"client config is not a valid dataclass: {cfg_cli}", "ConfigReader")
        return None
    for field in fields(cfg_cli):
        name = field.name
        val = _get_normalized_value(result, cfg_cli, name)
        if val is not None:
            setattr(result, name, val)
            log_debug(f"cli_update for {target} name={name}, val={val}", "ConfigReader")
    return result


def _get_normalized_value(obj_dest, obj_src, name: str) -> Optional[Any]:
    val = getattr(obj_src, name)
    if val is not None:
        extracted = getattr(obj_dest, name)
        if type(extracted) is bool:
            lowername = str(val).lower()
            if lowername in ("true", "false"):
                val = True if lowername == "true" else False
        elif type(extracted) is list:
            if isinstance(getattr(obj_src, name), list):
                testval = "".join(val)
                if isinstance(testval, str):
                    if testval.startswith("[") and testval.endswith("]"):
                        testval = testval[1:-1]
                        if testval.startswith("(") and testval.endswith(")"):
                            testval = testval[1:-1]
                            if "," in testval:
                                arr = testval.split(sep=",")
                                val = [(arr[0], arr[1])]
    return val


def check_work_path(work_path: str) -> str:
    if work_path == "":
        testpaths = GLOBAL_WORKPATHS
        for testpath in testpaths:
            if os.path.exists(f"{testpath}/templates") or testpath == os.getcwd():
                work_path = testpath
                break
    if work_path == "":
        log_debug(f"Global work_path search space: {GLOBAL_WORKPATHS}", "ConfigReader")
        log_info(f"Using searched work_path: {work_path}", "ConfigReader")
    else:
        log_info(f"Using supplied work_path: {work_path}", "ConfigReader")
    return work_path


def get_configs() -> list[TaskConfig]:
    result = []
    work_path, template_name, template_overlay = get_required_template_args()
    if work_path is None:
        work_path = os.getcwd()
    work_path = check_work_path(work_path)
    if work_path is not None:
        cfg_sys = get_cfg_sys(work_path)
        if template_overlay == "":
            cfg = get_config(cfg_sys, template_name, template_overlay)
            result.append(cfg)
        elif template_overlay != "*":
            result += get_configs_overlay_list(cfg_sys, template_name, template_overlay)
        elif template_overlay == "*":
            result += get_configs_overlay_all(cfg_sys, template_name)
    else:
        sys.exit(1)
    return result


def get_required_template_args() -> tuple[str, str, str]:
    cli_target = get_cli_group("target")
    if cli_target is None:
        return "", "", ""

    work_path = ""
    template_name = ""
    template_overlay = ""
    if isinstance(cli_target, TargetArgs):
        if cli_target.template is None:
            template_name = DEFAULT_TEMPLATE
            template_overlay = DEFAULT_TEMPLATE_OVERLAY
            log_debug(
                f"Use template : {template_name} ({template_overlay})", "ConfigReader"
            )
        else:
            template_name = cli_target.template
            template_overlay = cli_target.template_overlay
            log_debug(
                f"Use template : {template_name} ({template_overlay})", "ConfigReader"
            )
        if cli_target.work_path not in (None, ""):
            work_path = cli_target.work_path
        else:
            pass

    return work_path, template_name, template_overlay


def get_configs_overlay_list(
    cfg_sys, template_name: str, template_overlay: str
) -> list[TaskConfig]:
    result = []
    if "," in template_overlay:
        log_debug(f"Using multiple overlays: {template_overlay}")
        names = template_overlay.split(",")
        syspath = cfg_sys.path_templates
        path = f"{syspath}/iso/{template_name}"
        overlays = list_overlays(path)
        for overlay in overlays:
            log_debug(f"Using names: {overlay}")
            if overlay in names:
                cfg = get_config(cfg_sys, template_name, overlay)
                if cfg is not None:
                    cfg.target.template_overlay = overlay
                    result.append(cfg)
    else:
        log_debug(f"Using single overlay: {template_overlay}")
        cfg = get_config(cfg_sys, template_name, template_overlay)
        result.append(cfg)
    return result


def get_configs_overlay_all(cfg_sys, template_name: str) -> list[TaskConfig]:
    result = []
    syspath = cfg_sys.path_templates
    path = f"{syspath}/iso/{template_name}"
    overlays = list_overlays(path)
    for overlay in overlays:
        cfg = get_config(cfg_sys, template_name, overlay)
        if cfg is not None:
            cfg.target.template_overlay = overlay
            result.append(cfg)
    return result


def get_config(
    cfg_sys: SysConfig, template_name: str, template_overlay: str
) -> Optional[TaskConfig]:
    cfg_target = _match_group(
        "target", template_name, cfg_sys.path_templates, template_overlay
    )
    if cfg_target is None or isinstance(cfg_target, TargetArgs) is False:
        log_error(f"Matched target config invalid: {cfg_target}", "ConfigReader")
        return None
    cfg_env = _match_group(
        "env", template_name, cfg_sys.path_templates, template_overlay
    )
    if cfg_env is None or isinstance(cfg_env, EnvironmentArgs) is False:
        log_error(f"Matched env config invalid: {cfg_env}", "ConfigReader")
        return None
    cfg_run = _match_group(
        "run", template_name, cfg_sys.path_templates, template_overlay
    )
    if cfg_run is None or isinstance(cfg_run, RunArgs) is False:
        log_error(f"Matched run config invalid: {cfg_run}", "ConfigReader")
        return None
    cfg_ssh = _match_group(
        "addon_ssh", template_name, cfg_sys.path_templates, template_overlay
    )
    if cfg_ssh is None or isinstance(cfg_ssh, AddonArgsSsh) is False:
        log_error(f"Matched addon_ssh config invalid: {cfg_ssh}", "ConfigReader")
        return None
    cfg_grub = _match_group(
        "addon_grub", template_name, cfg_sys.path_templates, template_overlay
    )
    if cfg_grub is None or isinstance(cfg_grub, AddonArgsGrub) is False:
        log_error(f"Matched addon_grub config invalid: {cfg_grub}", "ConfigReader")
        return None
    cfg_post = _match_group(
        "addon_postinstall", template_name, cfg_sys.path_templates, template_overlay
    )
    if cfg_post is None or isinstance(cfg_post, AddonArgsPostinstall) is False:
        log_error(
            f"Matched addon_postinstall config invalid: {cfg_post}", "ConfigReader"
        )
        return None
    cfg_answer = _match_group(
        "addon_answerfile", template_name, cfg_sys.path_templates, template_overlay
    )
    if cfg_answer is None or isinstance(cfg_answer, AddonArgsAnswerFile) is False:
        log_error(
            f"Matched addon_answerfile config invalid: {cfg_answer}", "ConfigReader"
        )
        return None
    cfg_addons = AddonArgs(cfg_answer, cfg_ssh, cfg_grub, cfg_post)
    return TaskConfig(
        sys=cfg_sys, addons=cfg_addons, target=cfg_target, run=cfg_run, env=cfg_env
    )
