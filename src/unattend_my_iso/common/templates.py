import os
from pathlib import Path
from typing import Any, Optional
from unattend_my_iso.core.reader.reader_toml import TomlReader
from unattend_my_iso.common.config import TemplateConfig
from unattend_my_iso.common.logging import log_error, log_info, log_warn
from unattend_my_iso.common.const import (
    APP_VERSION,
    TEMPLATE_NAME,
    TEMPLATE_PREFIX,
    TEMPLATE_SUFFIX,
)

CLSNAME = "TemplateReader"


def read_templates_isos(parent_folder: str) -> dict[str, TemplateConfig]:
    result = {}
    if os.path.exists(parent_folder):
        for entry in os.scandir(parent_folder):
            if entry.is_dir():
                dir_template = Path(entry.path).resolve()
                full = f"{dir_template}/{TEMPLATE_NAME}"
                overlays = list_overlay_files(dir_template.as_posix())
                if os.path.exists(full):
                    config_template = read_template_iso(full, overlays)
                    if config_template is not None:
                        result[config_template.name] = config_template
    else:
        log_error(f"Template folder not valid: {parent_folder}", CLSNAME)
    return result


def list_overlay_files(parent_folder: str) -> list[str]:
    result = []
    if os.path.exists(parent_folder):
        for entry in os.scandir(parent_folder):
            if entry.is_dir() is False:
                if entry.name != TEMPLATE_NAME:
                    if entry.name.startswith(TEMPLATE_PREFIX):
                        if entry.name.endswith(TEMPLATE_SUFFIX):
                            result.append(entry.name)
    else:
        log_error(f"Template folder not valid: {parent_folder}", CLSNAME)
    return result


def list_overlays(parent_folder: str) -> list[str]:
    result = []
    for overlayfile in list_overlay_files(parent_folder):
        overlay = overlayfile.removeprefix(TEMPLATE_PREFIX).removesuffix(
            TEMPLATE_SUFFIX
        )
        result.append(overlay)
    result.sort()
    return result


def read_template_iso(file: str, overlays: list[str]) -> Optional[TemplateConfig]:
    reader = TomlReader()
    toml = reader.read_toml_file(file)
    if toml is not None:
        cfg = TemplateConfig(
            **toml["description"], name_overlay="", files_overlay=overlays
        )
        if cfg.config_version == APP_VERSION:
            return cfg
        else:
            log_warn(
                (
                    f"Template config version does not match for {cfg.name:10}: "
                    f"{APP_VERSION} vs {cfg.config_version}"
                ),
                CLSNAME,
            )
            return None
    else:
        log_error("Template config is not valid", CLSNAME)
    return None


def read_template_group(file: str, target: str) -> dict[str, Any]:
    reader = TomlReader()
    toml = reader.read_toml_file(file)
    if toml is not None:
        if target in toml:
            return toml[target]
    else:
        log_error(f"Group config is not valid: {file} -> {target} with {toml}", CLSNAME)
    return {}
