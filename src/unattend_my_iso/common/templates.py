import os
from pathlib import Path
from typing import Any, Optional
from unattend_my_iso.common.config import TemplateConfig
from unattend_my_iso.common.logging import log_error
from unattend_my_iso.core.reader.toml_reader import TomlReader


def read_templates_isos(parent_folder: str) -> dict[str, TemplateConfig]:
    result = {}
    for entry in os.scandir(parent_folder):
        if entry.is_dir():
            dir = Path(entry.path).resolve()
            full = f"{dir}/desc.toml"
            config_template = read_template_iso(full)
            if config_template is not None:
                result[config_template.name] = config_template
    return result


def read_template_iso(file: str) -> Optional[TemplateConfig]:
    reader = TomlReader()
    toml = reader.read_toml_file(file)
    if toml is not None:
        return TemplateConfig(**toml["description"])
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
        log_error(f"Group config is not valid: {target} with {toml}")
    return {}
