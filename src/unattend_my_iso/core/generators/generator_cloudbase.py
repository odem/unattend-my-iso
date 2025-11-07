import yaml
import json
from dataclasses import dataclass, asdict
from typing import List
from datetime import date
from unattend_my_iso.common.logging import log_error, log_info
from unattend_my_iso.core.files.file_manager import UmiFileManager
from unattend_my_iso.core.subprocess.caller import run

DIR_OUT = "C:"
FILE_CALC = "calc.exe"
FILE_AS = f"{DIR_OUT}\\autostart.ps1"
DIR_CB = "C:/Program Files/Cloudbase Solutions/Cloudbase-Init"
REG_RUN = "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
REG_CB = "HKLM:\\SOFTWARE\\Cloudbase Solutions\\Cloudbase-Init"


@dataclass
class CIBaseUser:
    name: str
    gecos: str
    primary_group: str
    groups: str
    passwd: str
    inactive: bool
    expiredate: date


@dataclass
class CIBaseConfig:
    ci_users: list[CIBaseUser]
    ci_uuid: str
    ci_hostname: str
    ci_dir: str
    ci_runcmd: list[str]
    ci_writefiles: list
    ci_isoname: str


@dataclass
class CICommandLineArguments:
    args: List[str]

    def tostring(self) -> str:
        return " ".join(self.args)

    @staticmethod
    def run_calc():
        return CICommandLineArguments([FILE_CALC])

    @staticmethod
    def run_cmd(cmd: str):
        arr = cmd.split(" ")
        return CICommandLineArguments(arr)

    @staticmethod
    def run_cloudbase(dir: str):
        return CICommandLineArguments(
            [
                "&",
                f'"{dir}/Python/Scripts/cloudbase-init.exe"',
                "--config-file",
                f'"{dir}/conf/cloudbase-init.conf"',
                "--debug",
            ]
        )

    @staticmethod
    def log_text(dir: str, text: str):
        return CICommandLineArguments(
            [
                "Write-Output",
                f'"{text}"',
                "|",
                "Out-File",
                "-FilePath",
                f'"{dir}/script-output.txt"',
            ]
        )

    @staticmethod
    def reg_del(path: str, name: str):
        return CICommandLineArguments(
            [
                "Remove-ItemProperty",
                "-Path",
                path,
                "-Name",
                f'"{name}"',
            ]
        )

    @staticmethod
    def run_powershell(file: str):
        return CICommandLineArguments(
            [
                "powershell.exe",
                "-WindowStyle",
                "Hidden",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                f"{file}",
            ]
        )

    @staticmethod
    def reg_add(path: str, name: str, value: list[str]):
        args = [
            "Set-ItemProperty",
            "-Path",
            f'"{path}"',
            "-Name",
            f'"{name}"',
            "-Value",
        ]
        args.extend(value)
        if args is not None:
            return CICommandLineArguments(args)
        return CICommandLineArguments([])

    @staticmethod
    def build_iso(dir: str, name: str):
        return CICommandLineArguments(
            [
                "genisoimage",
                "-output",
                f"{dir}/{name}",
                "-volid",
                "config-2",
                "-joliet",
                "-rock",
                "-graft-points",
                f"openstack={dir}/openstack",
            ]
        )


@dataclass
class CIWriteFile:
    path: str
    content: List[CICommandLineArguments]

    def tostring(self) -> str:
        yaml_content = ""
        for command in self.content:
            yaml_content += f"\n{command.tostring()}"
        return yaml_content


@dataclass
class CIRunCmd:
    commands: List[CICommandLineArguments]

    def tostring(self) -> str:
        yaml_content = ""
        for command in self.commands:
            yaml_content += "\n".join(command.args)
        return yaml_content


class UmiCloudBaseGenerator:
    def __init__(self) -> None:
        self.files = UmiFileManager()

    def create_openstack_iso(self, cfg: CIBaseConfig) -> bool:
        cmd = CICommandLineArguments.build_iso(cfg.ci_dir, cfg.ci_isoname)
        proc = run(cmd.args, text=True, capture_output=True)
        if proc.returncode != 0:
            log_error(f"{proc.stdout}{proc.stderr}", "CloudInit")
        return True

    def create_openstack_dir(self, cfg: CIBaseConfig) -> bool:
        vm_dir = cfg.ci_dir
        openstack_dir = f"{vm_dir}/openstack"
        latest_dir = f"{openstack_dir}/latest"
        filename_md = f"{latest_dir}/meta_data.json"
        filename_user = f"{latest_dir}/user_data"
        meta_data = self.create_meta_data(cfg)
        user_data = self.create_user_data(cfg)
        self.files.rm(openstack_dir)
        self.files.makedirs(latest_dir)
        self.files.append_to_file(filename_md, meta_data)
        self.files.append_to_file(filename_user, user_data)
        return True

    def create_meta_data(self, cfg: CIBaseConfig) -> str:
        meta_data = {"uuid": cfg.ci_uuid, "hostname": cfg.ci_hostname}
        return json.dumps(meta_data, indent=4)

    def create_user_data(self, cfg: CIBaseConfig) -> str:
        write_files_data = self._create_write_files(cfg)
        runcmd_data = self._create_runcmds(cfg.ci_runcmd)
        cloud_config = {
            "users": [asdict(user) for user in cfg.ci_users],
            "runcmd": [runcmd.tostring() for runcmd in runcmd_data],
            "write_files": [
                {
                    **asdict(writefile),
                    "content": writefile.tostring(),
                }
                for writefile in write_files_data
            ],
        }
        yaml_text = yaml.dump(cloud_config, default_flow_style=False)
        full = f"#cloud-config\n{yaml_text}"
        return full

    def _create_write_files(self, config: CIBaseConfig) -> List[CIWriteFile]:
        result = []
        default_content = self._create_default_write_files(config)
        for file in config.ci_writefiles:
            filename = file[0]
            content = file[1]
            log_info(f"{filename} {content}")
            if content == "TEMPLATE-AUTOSTART":
                content = default_content
                result.append(CIWriteFile(path=filename, content=default_content))
            else:
                result.append(
                    CIWriteFile(
                        path=filename,
                        content=[CICommandLineArguments(content.split(" "))],
                    )
                )
        return result

    def _create_default_write_files(
        self, config: CIBaseConfig
    ) -> List[CICommandLineArguments]:
        reg_plugins = f'"{REG_CB}\\{config.ci_uuid}\\Plugins"'
        as_cmd = CICommandLineArguments.run_powershell(FILE_AS)

        return [
            CICommandLineArguments.reg_add(
                REG_RUN, "CIAutostart", [f'"{as_cmd.tostring()}"']
            ),
            CICommandLineArguments.reg_del(reg_plugins, "UserDataPlugin"),
            CICommandLineArguments.reg_del(reg_plugins, "LocalScriptsPlugin"),
            CICommandLineArguments.reg_del(reg_plugins, "SetHostNamePlugin"),
            CICommandLineArguments.run_cloudbase(DIR_CB),
            CICommandLineArguments.log_text(DIR_OUT, "Dummy text 123"),
        ]

    def _create_runcmds(self, cmd: list[str]) -> list[CIRunCmd]:
        result = []
        for single in cmd:
            result.append(
                CIRunCmd(commands=[CICommandLineArguments(single.split(" "))])
            )
        return result
