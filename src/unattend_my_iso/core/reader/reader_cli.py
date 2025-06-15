import argparse
import textwrap
from typing import Any, Optional
from unattend_my_iso.common.args import (
    AddonArgsAnswerFile,
    AddonArgsGrub,
    AddonArgsPostinstall,
    AddonArgsSsh,
    EnvironmentArgs,
    RunArgs,
    TargetArgs,
)


class CommandlineReader:
    def _create_cli_parser(self) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(
            prog="PROG",
            usage="%(prog)s [options]",
            formatter_class=argparse.RawTextHelpFormatter,
            description=textwrap.dedent("Builds and runs unattended iso images"),
            epilog="""\
    Examples:
    --------------------------------------------------

    Build ISO with template debian12:
        python3 -m src.unattend_my_iso.main -tt debian12
        -> PARAM: targetArgs.template STRING
    
    Build ISO with all overlays (*):
        python3 -m src.unattend_my_iso.main -tt debian12 -to "*"
        -> PARAM: targetArgs.overlay STRING
    
    Build ISO with 3 overlays (foo, bar and baz):
        python3 -m src.unattend_my_iso.main -tt debian12 -to "foo,bar,baz"
        -> PARAM: targetArgs.overlay STRING

    Build ISO manually:
        python3 -m src.unattend_my_iso.main -tt debian12 -tp extract
        python3 -m src.unattend_my_iso.main -tt debian12 -tp addons
        python3 -m src.unattend_my_iso.main -tt debian12 -tp irmod
        python3 -m src.unattend_my_iso.main -tt debian12 -tp iso
        -> PARAM: targetArgs.processor STRING

    Run ISO:
        python3 -m src.unattend_my_iso.main -tt debian12 -rov true -rD true -tp vm_start
        python3 -m src.unattend_my_iso.main -tt debian12 -rov true -rD true -tp vm_stop
        -> PARAM: targetArgs.processor STRING
        -> PARAM: runArgs.daemonize BOOLEAN
        -> PARAM: runArgs.clean_old_vm BOOLEAN

    Networking:
        python3 -m src.unattend_my_iso.main -tt debian12 -tp net_start
        python3 -m src.unattend_my_iso.main -tt debian12 -tp net_stop
        -> PARAM: targetArgs.processor STRING

    Working Directory:
        python3 -m src.unattend_my_iso.main -tt debian12 -tw /etc/umi
        -> PARAM: targetArgs.work_dir STRING

    Long parameter versions:
        python3 -m src.unattend_my_iso.main --template debian12
        -> PARAM: targetArgs.template STRING

    Verbosity:
        python3 -m src.unattend_my_iso.main -rv 3
        -> PARAM: RunArgs.verbosity INTEGER

            """,
        )
        return p

    def _create_cli_parser_all(self) -> argparse.ArgumentParser:
        p = self._create_cli_parser()
        self._create_parser_args_run(p)
        self._create_parser_args_target(p)
        self._create_parser_args_addon_answerfile(p)
        self._create_parser_args_addon_postinst(p)
        self._create_parser_args_addon_grub(p)
        self._create_parser_args_addon_ssh(p)
        return p

    def _create_cli_parser_group(self, name: str) -> argparse.ArgumentParser:
        p = self._create_cli_parser()
        if name == "run":
            self._create_parser_args_run(p)
        elif name == "env":
            self._create_parser_args_env(p)
        elif name == "target":
            self._create_parser_args_target(p)
        elif name == "addon_grub":
            self._create_parser_args_addon_grub(p)
        elif name == "addon_ssh":
            self._create_parser_args_addon_ssh(p)
        elif name == "addon_postinstall":
            self._create_parser_args_addon_postinst(p)
        elif name == "addon_answerfile":
            self._create_parser_args_addon_answerfile(p)
        return p

    def _create_parser_args_addon_grub(self, p: argparse.ArgumentParser):
        group_target = p.add_argument_group(
            "AddonArgsGrub",
            description="Defines the arguments for the iso bootloader grub",
        )
        group_target.add_argument(
            "-ge",
            "--grub_enabled",
            type=str,
            default=None,
            help="Enable or disable grub addon (true or false)",
        )
        group_target.add_argument(
            "-gT",
            "--grub_theme",
            type=str,
            default=None,
            help="Theme name for grub",
        )
        group_target.add_argument(
            "-gI",
            "--grub_icons",
            type=str,
            default=None,
            help="Icon theme name for grub",
        )
        group_target.add_argument(
            "-gi",
            "--initrd_list",
            type=list,
            default=None,
            help="List of inird to modify",
        )
        group_target.add_argument(
            "-gs",
            "--sleeptime",
            type=int,
            default=None,
            help="List of inird to modify",
        )
        group_target.add_argument(
            "-gt",
            "--timeout",
            type=int,
            default=None,
            help="List of inird to modify",
        )
        group_target.add_argument(
            "-gkla1",
            "--grub_kernel_lvm_alt1",
            type=int,
            default=None,
            help="Custom LVM Kernel 1",
        )
        group_target.add_argument(
            "-gkla2",
            "--grub_kernel_lvm_alt2",
            type=int,
            default=None,
            help="Custom LVM Kernel 2",
        )

    def _create_parser_args_addon_postinst(self, p: argparse.ArgumentParser):
        group_target = p.add_argument_group(
            "AddonArgsPostinstall",
            description="Defines the arguments for the postinstaller",
        )
        group_target.add_argument(
            "-pe",
            "--postinstall_enabled",
            type=str,
            default=None,
            help="Enable or disable postinstall addon (true or false)",
        )
        group_target.add_argument(
            "-pg",
            "--enable_grub_theme",
            type=str,
            default=None,
            help="Enable or disable grub theme in the target installation (true or false)",
        )
        group_target.add_argument(
            "-pc",
            "--create_config",
            type=str,
            default=None,
            help="Enable or disable a config to be copied into the target (true or false)",
        )
        group_target.add_argument(
            "-pau",
            "--auto_updates",
            type=int,
            default=None,
            help="Configures apt for auto updates",
        )
        group_target.add_argument(
            "-ppg",
            "--password_generate",
            type=int,
            default=None,
            help="Generate new initial passwords",
        )
        group_target.add_argument(
            "-ppl",
            "--password_length",
            type=int,
            default=None,
            help="Length of generated password",
        )
        group_target.add_argument(
            "-ppc",
            "--password_charset",
            type=str,
            default=None,
            help="Charset to use for passwords",
        )
        group_target.add_argument(
            "-pje",
            "--joblist_early",
            type=str,
            default=None,
            help="Jobs to execute before copied scripts",
        )
        group_target.add_argument(
            "-pjl",
            "--joblist_late",
            type=str,
            default=None,
            help="Jobs to execute after copied scripts",
        )
        group_target.add_argument(
            "-pa",
            "--copy_additional_scripts",
            type=str,
            default=None,
            help="Copies additional scripts (list)",
        )
        group_target.add_argument(
            "-px",
            "--exec_additional_scripts",
            type=str,
            default=None,
            help="Copies additional scripts (list)",
        )

    def _create_parser_args_addon_ssh(self, p: argparse.ArgumentParser):
        group_target = p.add_argument_group(
            "AddonArgsSsh",
            description="Defines the arguments for the ssh addon",
        )
        group_target.add_argument(
            "-se",
            "--ssh_enabled",
            type=str,
            default=None,
            help="Enable or disable ssh addon (true or false)",
        )
        group_target.add_argument(
            "-sK",
            "--keygen",
            type=str,
            default=None,
            help="Enable or disable keygen option (true or false)",
        )
        group_target.add_argument(
            "-sc",
            "--config_client",
            type=str,
            default=None,
            help="Name of copied client config",
        )
        group_target.add_argument(
            "-sd",
            "--config_daemon",
            type=str,
            default=None,
            help="Name of copied daemon config",
        )
        group_target.add_argument(
            "-sa",
            "--config_auth",
            type=str,
            default=None,
            help="Name of copied authorization file",
        )
        group_target.add_argument(
            "-sA",
            "--config_auth_append",
            type=str,
            default=None,
            help="Name of file which is appended to authorization file",
        )
        group_target.add_argument(
            "-sk",
            "--config_key",
            type=str,
            default=None,
            help="Name of keyfile being copied into target",
        )

    def _create_parser_args_addon_answerfile(self, p: argparse.ArgumentParser):
        group_target = p.add_argument_group(
            "AddonArgsAnswerfile",
            description="Defines the arguments for the answerfile",
        )
        group_target.add_argument(
            "-ae",
            "--answerfile_enabled",
            type=str,
            default=None,
            help="Enable or disable answerfile addon (true or false)",
        )
        group_target.add_argument(
            "-aEn",
            "--answerfile_enable_networking",
            type=str,
            default=None,
            help="Enable or disable networking during isntallation",
        )
        group_target.add_argument(
            "-aEd",
            "--answerfile_enable_dhcp",
            type=str,
            default=None,
            help="Enable or disable dhcp during isntallation",
        )
        group_target.add_argument(
            "-aEc",
            "--answerfile_enable_crypto",
            type=str,
            default=None,
            help="Enable or disable disk encryption",
        )
        group_target.add_argument(
            "-aEl",
            "--answerfile_enable_lvm",
            type=str,
            default=None,
            help="Enable or disable lvm",
        )
        group_target.add_argument(
            "-aECp",
            "--answerfile_confirm_partitioning",
            type=str,
            default=None,
            help="Confirms partitioning",
        )
        group_target.add_argument(
            "-aECr",
            "--answerfile_confirm_final_reboot",
            type=str,
            default=None,
            help="Confirms final reboot",
        )
        group_target.add_argument(
            "-aHc",
            "--answerfile_hook_dir_cdrom",
            type=str,
            default=None,
            help="Hook dir for cdrom",
        )
        group_target.add_argument(
            "-aHt",
            "--answerfile_hook_dir_target",
            type=str,
            default=None,
            help="Hook dir for target",
        )
        group_target.add_argument(
            "-aHf",
            "--answerfile_hook_filename",
            type=str,
            default=None,
            help="Hook filename",
        )
        group_target.add_argument(
            "-aid",
            "--install_disk",
            type=str,
            default=None,
            help="The disk to force installation to",
        )
        group_target.add_argument(
            "-alm",
            "--locale_multi",
            type=str,
            default=None,
            help="The locale to use",
        )
        group_target.add_argument(
            "-als",
            "--locale_string",
            type=str,
            default=None,
            help="The locale string to use",
        )
        group_target.add_argument(
            "-alk",
            "--locale_keyboard",
            type=str,
            default=None,
            help="The keyboard layout to use",
        )
        group_target.add_argument(
            "-ahn",
            "--host_name",
            type=str,
            default=None,
            help="The hostname to use",
        )
        group_target.add_argument(
            "-ahd",
            "--host_domain",
            type=str,
            default=None,
            help="The domain to use",
        )
        group_target.add_argument(
            "-anD",
            "--net_dhcp",
            type=str,
            default=None,
            help="Enables or disables dhcp (true or false)",
        )
        group_target.add_argument(
            "-ani",
            "--net_ip",
            type=str,
            default=None,
            help="The ip to use",
        )
        group_target.add_argument(
            "-anm",
            "--net_mask",
            type=str,
            default=None,
            help="The netmask to use",
        )
        group_target.add_argument(
            "-ang",
            "--net_gateway",
            type=str,
            default=None,
            help="The gateway to use",
        )
        group_target.add_argument(
            "-and",
            "--net_dns",
            type=str,
            default=None,
            help="The dns to use",
        )
        group_target.add_argument(
            "-adp",
            "--disk_password",
            type=str,
            default=None,
            help="The crypto password to use",
        )
        group_target.add_argument(
            "-adl",
            "--disk_lvm_vg",
            type=str,
            default=None,
            help="The name of the lvm volume group",
        )
        group_target.add_argument(
            "-atu",
            "--time_utc",
            type=str,
            default=None,
            help="Use UTC clock (true or false)",
        )
        group_target.add_argument(
            "-atz",
            "--time_zone",
            type=str,
            default=None,
            help="The timezone to use",
        )
        group_target.add_argument(
            "-atn",
            "--time_ntp",
            type=str,
            default=None,
            help="Use NTP synchronization (true or false)",
        )
        group_target.add_argument(
            "-aure",
            "--user_root_enabled",
            type=str,
            default=None,
            help="Enable root user (true or false)",
        )
        group_target.add_argument(
            "-aurp",
            "--user_root_pw",
            type=str,
            default=None,
            help="The root password to use",
        )
        group_target.add_argument(
            "-auoe",
            "--user_other_enabled",
            type=str,
            default=None,
            help="Enable other user (true or false)",
        )
        group_target.add_argument(
            "-auon",
            "--user_other_name",
            type=str,
            default=None,
            help="The other user name to use",
        )
        group_target.add_argument(
            "-auof",
            "--user_other_fullname",
            type=str,
            default=None,
            help="The other user fullname to use",
        )
        group_target.add_argument(
            "-auop",
            "--user_other_pw",
            type=str,
            default=None,
            help="The other user password to use",
        )
        group_target.add_argument(
            "-api",
            "--packages_install",
            type=str,
            default=None,
            help="The packages to install",
        )
        group_target.add_argument(
            "-aau",
            "--additional_users",
            type=str,
            default=None,
            help="Additional users to add",
        )
        group_target.add_argument(
            "-asu",
            "--sudo_users",
            type=str,
            default=None,
            help="Additional users to add",
        )
        group_target.add_argument(
            "-ag",
            "--grub_install_device",
            type=str,
            default=None,
            help="The device to install grub to",
        )
        group_target.add_argument(
            "-aiop",
            "--include_offline_packages",
            type=str,
            default=None,
            help="The packages to include",
        )

    def _create_parser_args_run(self, p: argparse.ArgumentParser):
        group_target = p.add_argument_group(
            "RunArgs",
            description="Defines the arguments for running a vm",
        )
        group_target.add_argument(
            "-rn",
            "--vmname",
            type=str,
            default=None,
            help="Name of the vm",
        )
        group_target.add_argument(
            "-rv",
            "--verbosity",
            type=int,
            default=None,
            help="Name of the vm (0=error,1=warn,2=info,3=debug)",
        )
        group_target.add_argument(
            "-rbu",
            "--build_user",
            type=str,
            default=None,
            help="The utilized user",
        )
        group_target.add_argument(
            "-rbh",
            "--build_homedir",
            type=str,
            default=None,
            help="The homefolder to use",
        )
        group_target.add_argument(
            "-rD",
            "--daemonize",
            type=str,
            default=None,
            help="Non-blocking call to qemu-kvm via Popen (true or false)",
        )
        group_target.add_argument(
            "-rbU",
            "--uefi_boot",
            type=str,
            default=None,
            help="Use uefi boot to run the iso (true or false)",
        )
        group_target.add_argument(
            "-rbC",
            "--cdrom_boot",
            type=str,
            default=None,
            help="Use cdrom to boot vm (true or false)",
        )
        group_target.add_argument(
            "-rV",
            "--uefi_ovmf_vars",
            type=str,
            default=None,
            help="Use custom path to omvf vars section",
        )
        group_target.add_argument(
            "-rC",
            "--uefi_ovmf_code",
            type=str,
            default=None,
            help="Use custom path to omvf code section",
        )
        group_target.add_argument(
            "-rc",
            "--res_cpu",
            type=int,
            default=None,
            help="Use custom cpu amount",
        )
        group_target.add_argument(
            "-rm",
            "--res_mem",
            type=int,
            default=None,
            help="Use custom memory amount",
        )
        group_target.add_argument(
            "-rdn",
            "--disks",
            type=str,
            default=None,
            help="List of disks",
        )
        group_target.add_argument(
            "-rnP",
            "--net_ports",
            type=list,
            default=None,
            help="Use custom port forwardings",
        )
        group_target.add_argument(
            "-rnD",
            "--net_devs",
            type=list,
            default=None,
            help="Use custom network devices",
        )
        group_target.add_argument(
            "-rnB",
            "--net_bridges",
            type=list,
            default=None,
            help="Use custom network bridges",
        )
        group_target.add_argument(
            "-rnpf",
            "--net_prepare_fw",
            type=str,
            default=None,
            help="Setup firewall before running vm",
        )
        group_target.add_argument(
            "-rnpn",
            "--net_prepare_nics",
            type=str,
            default=None,
            help="Setup nics before running vm",
        )
        group_target.add_argument(
            "-rnpb",
            "--net_prepare_bridges",
            type=str,
            default=None,
            help="Setup bridges before running vm",
        )
        group_target.add_argument(
            "-rov",
            "--clean_old_vm",
            type=str,
            default=None,
            help="Clean old vm before running a new one",
        )
        return group_target

    def _create_parser_args_env(self, p: argparse.ArgumentParser):
        group_target = p.add_argument_group(
            "TargetArgs",
            description="Defines the target to build or run",
        )
        group_target.add_argument(
            "-ea",
            "--env_args",
            type=str,
            default=None,
            help="Environment variables",
        )
        return group_target

    def _create_parser_args_target(self, p: argparse.ArgumentParser):
        group_target = p.add_argument_group(
            "TargetArgs",
            description="Defines the target to build or run",
        )
        group_target.add_argument(
            "-tf",
            "--file_prefix",
            type=str,
            default=None,
            help="Prefix for output file",
        )
        group_target.add_argument(
            "-te",
            "--file_extension",
            type=str,
            default=None,
            help="Extension for output file",
        )
        group_target.add_argument(
            "-tm",
            "--file_mbr",
            type=str,
            default=None,
            help="path to mbr file",
        )
        group_target.add_argument(
            "-tt",
            "--template",
            type=str,
            default=None,
            help="Template name",
        )
        group_target.add_argument(
            "-to",
            "--template_overlay",
            type=str,
            default=None,
            help="Overlay name",
        )
        group_target.add_argument(
            "-tp",
            "--proctype",
            type=str,
            default=None,
            help="The processor type (run, extract, addons, irmod, iso, all)",
        )
        group_target.add_argument(
            "-tw",
            "--work_path",
            type=str,
            default=None,
            help="The work_path to user",
        )
        group_target.add_argument(
            "-tc",
            "--cmds",
            type=str,
            default=None,
            help="Commands to be executed",
        )
        group_target.add_argument(
            "-tC",
            "--cmd",
            type=str,
            default=None,
            help="Command to be executed",
        )
        return group_target

    def read_cli_group(self, name: str) -> Optional[Any]:
        p = self._create_cli_parser_group(name)
        args = p.parse_known_args()
        kwargs = args[0]._get_kwargs()
        all = {}
        for item in kwargs:
            all[item[0]] = item[1]
        if name == "run":
            return RunArgs(**all)
        elif name == "env":
            return EnvironmentArgs(**all)
        elif name == "target":
            return TargetArgs(**all)
        elif name == "addon_grub":
            return AddonArgsGrub(**all)
        elif name == "addon_ssh":
            return AddonArgsSsh(**all)
        elif name == "addon_answerfile":
            return AddonArgsAnswerFile(**all)
        elif name == "addon_postinstall":
            return AddonArgsPostinstall(**all)
        return None
