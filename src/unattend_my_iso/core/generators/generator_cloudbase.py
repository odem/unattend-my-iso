import os
import yaml
import json
from dataclasses import dataclass, asdict
from typing import List
from datetime import date
from unattend_my_iso.common.logging import log_error
from unattend_my_iso.core.files.file_manager import UmiFileManager
from unattend_my_iso.core.subprocess.caller import run


# Define a CloudBaseConfig dataclass to hold all environment-specific variables (now lowercase)
@dataclass
class CloudBaseConfig:
    ci_adminname: str
    ci_group_admin: str
    ci_adminpass: str
    ci_username: str
    ci_userpass: str
    ci_group_users: str
    ci_uuid: str
    ci_hostname: str
    ci_dir: str
    ci_isoname: str = "cloud-init.iso"


# Define the CloudBaseUser dataclass
@dataclass
class CloudBaseUser:
    name: str
    gecos: str
    primary_group: str
    groups: str
    passwd: str
    inactive: bool
    expiredate: date


# Define the CommandLineArguments dataclass to store command arguments
@dataclass
class CommandLineArguments:
    args: List[str]  # List of strings (each representing an argument for the command)


# Define the WriteFile dataclass with content as a list of CommandLineArguments
@dataclass
class WriteFile:
    path: str
    content: List[CommandLineArguments]  # List of CommandLineArguments instances

    # Convert the content to a YAML block-style string (using pipe)
    def to_yaml_content(self) -> str:
        yaml_content = ""
        for command in self.content:
            yaml_content += "\n  - " + " ".join(
                command.args
            )  # Each command as a string with space separation
        return yaml_content


# Define the RunCmd dataclass using CommandLineArguments
@dataclass
class RunCmd:
    command: List[CommandLineArguments]  # List of CommandLineArguments instances


class UmiCloudBaseGenerator:
    def __init__(self) -> None:
        self.files = UmiFileManager()
        self.extender = "\\\n    "

    # Helper function to create CloudBaseUsers based on the CloudBaseConfig
    def create_cloudbase_users(self, config: CloudBaseConfig) -> List[CloudBaseUser]:
        return [
            CloudBaseUser(
                name=config.ci_adminname,
                gecos=f"CI {config.ci_adminname}",
                primary_group=config.ci_group_admin,
                groups=config.ci_group_admin,
                passwd=config.ci_adminpass,
                inactive=False,
                expiredate=date(2099, 10, 1),
            ),
            CloudBaseUser(
                name=config.ci_username,
                gecos=f"CI {config.ci_username}",
                primary_group=config.ci_group_users,
                groups=config.ci_group_users,
                passwd=config.ci_userpass,
                inactive=False,
                expiredate=date(2099, 10, 1),
            ),
        ]

    # Helper function to create write_files based on the CloudBaseConfig
    def create_write_files(self, config: CloudBaseConfig) -> List[WriteFile]:
        reg_run = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        return [
            WriteFile(
                path=f"C:/Users/{config.ci_username}/autostart.ps1",
                content=[
                    # Each command is a CommandLineArguments object
                    CommandLineArguments(
                        [
                            "Write-Output",
                            '"This script was run by cloudbase-init"',
                            "|",
                            "Out-File",
                            "-FilePath",
                            f"C:/Users/{config.ci_username}/script-output.txt",
                        ]
                    ),
                    CommandLineArguments(
                        [
                            "Remove-ItemProperty",
                            "-Path",
                            f'"HKLM:\\{reg_run}\\{config.ci_uuid}\\Plugins"',
                            "-Name",
                            '"UserDataPlugin"',
                        ]
                    ),
                    CommandLineArguments(
                        [
                            "Set-ItemProperty",
                            "-Path",
                            f'"HKCU:\\{reg_run}"',
                            "-Name",
                            '"CIAutostart"',
                            "-Value",
                            f'"powershell.exe -ExecutionPolicy Bypass -File C:/Users/{config.ci_username}/autostart.ps1"',
                        ]
                    ),
                    CommandLineArguments(
                        [
                            "cd",
                            '"C:\\Program Files\\Cloudbase Solutions\\Cloudbase-Init\\Python\\Scripts\\cloudbase-init.exe"',
                        ]
                    ),
                    CommandLineArguments(
                        [
                            "./cloudbase-init.exe",
                            "--config-file",
                            "./cloudbase-init.conf",
                            "--debug",
                        ]
                    ),
                ],
            )
        ]

    # Helper function to create runcmds based on the CloudBaseConfig
    def create_runcmds(self, config: CloudBaseConfig) -> List[RunCmd]:
        return [
            RunCmd(
                command=[
                    CommandLineArguments(
                        [
                            "powershell.exe",
                            "-ExecutionPolicy",
                            "Bypass",
                            "-File",
                            f"C:/Users/{config.ci_username}/autostart.ps1",
                        ]
                    )
                ]
            )
        ]

    def create_openstack_iso(self, cfg: CloudBaseConfig) -> bool:
        cmd = [
            "genisoimage",
            "-output",
            f"{cfg.ci_dir}/{cfg.ci_isoname}",
            "-volid",
            "config-2",
            "-joliet",
            "-rock",
            "-graft-points",
            f"openstack={cfg.ci_dir}/openstack",
        ]
        proc = run(cmd, text=True, capture_output=True)
        if proc.returncode != 0:
            log_error(f"{proc.stdout}{proc.stderr}", "CloudInit")
        return True

    def create_openstack_dir(self, cfg: CloudBaseConfig) -> bool:
        meta_data = self.create_meta_data(cfg)
        user_data = self.create_user_data(cfg)
        vm_dir = cfg.ci_dir
        openstack_dir = f"{vm_dir}/openstack"
        latest_dir = f"{openstack_dir}/latest"
        filename_md = f"{latest_dir}/meta_data.json"
        filename_user = f"{latest_dir}/user_data"
        self.files.rm(latest_dir)
        self.files.makedirs(latest_dir)
        self.files.append_to_file(filename_md, meta_data)
        self.files.append_to_file(filename_user, user_data)
        return True

    def create_meta_data(self, cfg: CloudBaseConfig) -> str:
        # The JSON data structure for meta_data
        meta_data = {"uuid": cfg.ci_uuid, "hostname": cfg.ci_hostname}
        return json.dumps(meta_data, indent=4)

    def create_user_data(self, cfg: CloudBaseConfig) -> str:

        # Now we can generate all the necessary components using the CloudBaseConfig
        cloudbase_users_data = self.create_cloudbase_users(cfg)
        write_files_data = self.create_write_files(cfg)
        runcmd_data = self.create_runcmds(cfg)

        # Combine everything into a dictionary structure
        cloud_config = {
            "users": [asdict(user) for user in cloudbase_users_data],
            "write_files": [
                {
                    **asdict(writefile),
                    "content": writefile.to_yaml_content(),
                }
                for writefile in write_files_data
            ],
            "runcmd": [
                {
                    **asdict(runcmd),
                    "command": [cmd.args for cmd in runcmd.command],
                }
                for runcmd in runcmd_data
            ],
        }

        # Serialize to YAML
        yaml_text = yaml.dump(cloud_config, default_flow_style=False)
        full = f"#cloud-config\n{yaml_text}"
        return full
