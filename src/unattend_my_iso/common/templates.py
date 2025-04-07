import os
from pathlib import Path
from typing import Any, Optional
from unattend_my_iso.common.config import TemplateConfig
from unattend_my_iso.common.logging import log_debug, log_error
from unattend_my_iso.core.reader.toml_reader import TomlReader


def read_templates_isos(parent_folder: str) -> dict[str, TemplateConfig]:
    result = {}
    for entry in os.scandir(parent_folder):
        if entry.is_dir():
            dir_template = Path(entry.path).resolve()
            full = f"{dir_template}/desc.toml"
            overlays = list_overlays(dir_template.as_posix())
            if os.path.exists(full):
                config_template = read_template_iso(full, overlays)
                if config_template is not None:
                    # log_debug(f"Adding Template: {config_template.name}")
                    result[config_template.name] = config_template
    return result


def list_overlays(parent_folder: str) -> list[str]:
    result = []
    for entry in os.scandir(parent_folder):
        if entry.is_dir() is False:
            if entry.name != "desc.toml":
                if entry.name.startswith("desc."):
                    if entry.name.endswith(".toml"):
                        result.append(entry.name)
    return result


def read_template_iso(file: str, overlays: list[str]) -> Optional[TemplateConfig]:
    reader = TomlReader()
    toml = reader.read_toml_file(file)
    if toml is not None:
        return TemplateConfig(
            **toml["description"], name_overlay="", files_overlay=overlays
        )
    else:
        log_error("Template config is not valid")
    return None


def read_template_group(file: str, target: str) -> dict[str, Any]:
    reader = TomlReader()
    toml = reader.read_toml_file(file)
    if toml is not None:
        if target in toml:
            return toml[target]
    else:
        log_error(f"Group config is not valid: {file} -> {target} with {toml}")
    return {}
