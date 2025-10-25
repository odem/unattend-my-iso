from dataclasses import dataclass
import os
import subprocess
from typing import Optional
from unattend_my_iso.core.generators.generator_cloudbase import CloudBaseConfig
from unattend_my_iso.core.generators.generator_qemu import UmiQemuCommands
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.core.net.net_manager import UmiNetworkManager
from unattend_my_iso.core.vm.hypervisor_base import HypervisorArgs, UmiHypervisorBase
from unattend_my_iso.common.logging import log_debug, log_error, log_info
from unattend_my_iso.core.subprocess.caller import (
    check_call,
    run,
    run_background,
    CalledProcessError,
    Popen,
    PIPE,
    DEVNULL,
)


@dataclass
class ExecCommandInfo:
    name: str
    scope: str
    con: str
    cmd: str


class UmiHypervisorKvm(UmiHypervisorBase):
    def __init__(self) -> None:
        UmiHypervisorBase.__init__(self)
        self.net = UmiNetworkManager()

    def vm_exec_find_target_command(
        self, args: TaskConfig, args_hv: HypervisorArgs
    ) -> Optional[ExecCommandInfo]:
        target = args.addons.cmd.cmd
        cmds = args.addons.cmd.cmds
        for cmd in cmds:
            if isinstance(cmd, dict):
                info = ExecCommandInfo(**cmd)
                log_info(f"Parsed CMD: {info.name}")
                if info.name == target:
                    log_info(f"Found CMD: {info}")
                    return info
        return None

    def vm_exec_build_shell_cmd(
        self, info: ExecCommandInfo, args: TaskConfig
    ) -> list[str]:
        result = []
        if info.scope == "":
            # target = "mps"
            if info.con == "nat":
                host = "localhost"
                ports = args.run.net_ports
                ports_ssh = [port[0] for port in ports if port[1] == "22"]
                if len(ports_ssh) >= 0:
                    port = ports_ssh[0]
                    con = f"ssh -p {port} root@{host} {info.cmd}"
                    result.append(con)
            elif ":" in info.con:
                parts = info.con.split(":")
                host = parts[0]
                port = parts[1]
                con = f"ssh -p {port} root@{host} {info.cmd}"
                result.append(con)
            else:
                host = info.con
                port = 22
                con = f"ssh -p {port} root@{host} {info.cmd}"
                result.append(con)

        return result

    def vm_exec(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        info = self.vm_exec_find_target_command(args, args_hv)
        if info is None:
            return False
        cmdlist = self.vm_exec_build_shell_cmd(info, args)
        for cmd in cmdlist:
            if check_call(cmd.split(" ")) == 0:
                return True
        return False

    def vm_runscript(self, runstring: str, args: TaskConfig) -> bool:
        if args.run.generate_run_script:
            vmdir = self.files._get_path_vm(args)
            runner_name = "run.bash"
            full_name = f"{vmdir}/{runner_name}"
            allstring = f"#!/bin/bash\n\n{runstring}"
            log_info(
                f"Running VM   : Create runscript at {full_name}",
                self.__class__.__qualname__,
            )
            if os.path.exists(full_name):
                os.remove(full_name)
            self.files.append_to_file(full_name, allstring)
            if os.path.exists(full_name):
                self.files.chmod(full_name, 755)
        return True

    def vm_run(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        gen = UmiQemuCommands()
        runcmd = gen.create_run_command(args, args_hv)
        log_info(
            f"Running VM   : {args_hv.name} (Daemonize: {args.run.daemonize})",
            self.__class__.__qualname__,
        )
        runstring = " ".join(runcmd)
        self.vm_runscript(runstring, args)
        final_cmd = []
        for cmd in runcmd:
            if cmd != gen.extender:
                final_cmd.append(cmd)
        if args.run.verbosity >= 4:
            log_debug(f"Run command  : {runstring}", self.__class__.__qualname__)
        if self.net.net_start(args_hv) is False:
            log_error(
                "Networking   : Could not setup network", self.__class__.__qualname__
            )
            return False

        if args.run.daemonize:
            return self.vm_run_nonblocking(final_cmd, args_hv)
        return self.vm_run_blocking(final_cmd, args_hv)

    def vm_stop(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        if os.path.exists(args_hv.pidfile):
            log_info(
                f"Stopping VM  : {args_hv.name} (Daemonize: {args.run.daemonize})",
                self.__class__.__qualname__,
            )
            stopcmd = ["sudo", "pkill", "-F", args_hv.pidfile]
            try:
                run(stopcmd, capture_output=True, text=True, check=True)
            except CalledProcessError as exe:
                log_error(f"Exception    : {exe}", self.__class__.__qualname__)
                return False
        if self.net.net_stop(args_hv) is False:
            log_error(
                "Networking   : Could not stop network",
                self.__class__.__qualname__,
            )
            return False
        return True

    def vm_exec_blocking(self, runcmd: list[str]) -> bool:
        run(
            runcmd,
            stdin=DEVNULL,
            stdout=subprocess.STDOUT,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        return True

    def vm_run_nonblocking(self, runcmd: list[str], args_hv: HypervisorArgs) -> bool:
        proc = run_background(
            runcmd, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, close_fds=True
        )
        self.vm_run_postsetup(proc, args_hv, False)
        return True

    def vm_run_blocking(self, runcmd: list[str], args_hv: HypervisorArgs) -> bool:

        proc = run_background(runcmd, stdout=PIPE, stderr=PIPE, text=True)
        self.vm_run_postsetup(proc, args_hv, True)
        log_info("\n\nRunning VM   : Press Ctrl+C to stop", self.__class__.__qualname__)
        return True

    def vm_run_postsetup(
        self, proc: Popen, args_hv: HypervisorArgs, wait: bool
    ) -> bool:
        if proc.pid <= 0:
            log_error(
                f"VM Error     : {proc.pid} -> {proc.stdin} {proc.stderr}",
                self.__class__.__qualname__,
            )
            return False
        log_info(f"Process PID  : {proc.pid}", self.__class__.__qualname__)
        if wait:
            try:
                stdout, stderr = proc.communicate()
                log_info(
                    f"VM exit     : stdout={stdout}, stderr={stderr}",
                    self.__class__.__qualname__,
                )
            except KeyboardInterrupt:
                log_info(f"VM stopped   : {args_hv.name}", self.__class__.__qualname__)
                proc.terminate()
                if self.net.net_stop(args_hv) is False:
                    return False
        return True

    def vm_prepare_disks(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        for disk in args_hv.disks:
            if isinstance(disk, list) and len(disk) >= 2:
                filename = disk[0]
                size = disk[1]
                if os.path.exists(filename) is False:
                    if self.vm_prepare_disk(args, filename, size) is False:
                        return False
            else:
                return False
        return True

    def vm_prepare_disk(self, args: TaskConfig, diskpath: str, size: str) -> bool:
        vmdir = self.files._get_path_vm(args)
        os.makedirs(vmdir, exist_ok=True)
        rmcmd = []
        if diskpath.endswith(".qcow2"):
            rmcmd = self.vm_prepare_disk_qcow(diskpath, size)
        elif diskpath.endswith(".raw"):
            rmcmd = self.vm_prepare_disk_raw(diskpath, size)
        if len(rmcmd) > 0:
            ret = run(rmcmd, capture_output=True, text=True)
            if ret.returncode == 0:
                log_debug(
                    f"Disk created with size {size} -> {diskpath}",
                    self.__class__.__qualname__,
                )
                return True
            log_error(
                f"Error while creating disk size {size} -> {diskpath}",
                self.__class__.__qualname__,
            )
        else:
            log_error(
                f"Invalid extension in diskpath: {diskpath}",
                self.__class__.__qualname__,
            )
        return False

    def vm_prepare_tpm(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        vmdir = self.files._get_path_vm(args)
        socketdir = f"{vmdir}/swtpm"
        if args_hv.vmtype == "windows":
            if os.path.exists(f"{socketdir}-socket"):
                run(["pkill", "-f", "swtpm"])
            os.makedirs(socketdir, exist_ok=True)
            runcmd = self._create_tpm_command(socketdir)
            Popen(
                runcmd,
                stdout=DEVNULL,
                stderr=DEVNULL,
                close_fds=True,
            )
            log_info(f"swtpm inst   : {socketdir}", self.__class__.__qualname__)
        return True

    def prepare_disk_efi(self, args: TaskConfig) -> bool:
        vmdir = f"{args.sys.path_vm}/{args.run.vmname}"
        varsname = os.path.basename(args.run.uefi_ovmf_vars)
        diskname = args.run.uefi_ovmf_vars
        if args.run.secure_boot:
            varsname = os.path.basename(args.run.uefi_ovmf_vars_ms)
            diskname = args.run.uefi_ovmf_vars_ms

        efidisk = f"{vmdir}/{varsname}"
        if os.path.exists(vmdir) is False:
            os.makedirs(vmdir)
        if os.path.exists(efidisk) is False:
            rmcmd = ["rm", efidisk]
            cpcmd = ["cp", diskname, efidisk]
            run(rmcmd, capture_output=True, text=True)
            copied = run(cpcmd, capture_output=True, text=True)
            if copied.returncode != 0:
                log_error(
                    f"Error on copy disk: {diskname} to {efidisk}",
                    self.__class__.__qualname__,
                )
                return False
        return True

    def vm_get_args(self, args: TaskConfig, template: TemplateConfig) -> HypervisorArgs:
        vmdir = self.files._get_path_vm(args)
        pidfile = self.files._get_path_vmpid(args)
        cloudbase_config = CloudBaseConfig(
            ci_adminname=args.addons.answerfile.user_root_name,
            ci_group_admin=args.addons.answerfile.admin_group_name,
            ci_adminpass=args.addons.answerfile.user_root_pw,
            ci_username=args.addons.answerfile.user_other_name,
            ci_userpass=args.addons.answerfile.user_other_pw,
            ci_group_users=args.addons.answerfile.user_group_name,
            ci_uuid=args.run.ci_uuid,
            ci_hostname=args.addons.answerfile.host_name,
            ci_dir=vmdir,
        )
        disks = []
        for disk in args.run.disks:
            innerlist = disk
            innerlist[0] = f"{vmdir}/{innerlist[0]}"
            disks.append(innerlist)

        cdrom = ""
        if args.run.ci_enabled is True:
            self.ci_gen.create_openstack_dir(cloudbase_config)
            self.ci_gen.create_openstack_iso(cloudbase_config)
        if args.run.cdrom_boot is True:
            cdrom = self.files._get_path_isofile(args)
        return HypervisorArgs(
            args.target.template,
            template.iso_type,
            args.run.uefi_boot,
            cdrom,
            disks,
            args.run.net_devs,
            args.run.net_bridges,
            args.run.net_ports,
            args.run.uplink_dev,
            args.run.res_cpu,
            args.run.res_mem,
            args.run.net_prepare_fw,
            args.run.net_prepare_nics,
            args.run.net_prepare_bridges,
            pidfile,
            args.run.clean_old_vm,
            cloudbase_config,
        )

    def vm_prepare_disk_qcow(self, diskpath: str, size: str) -> list[str]:
        return [
            "qemu-img",
            "create",
            "-q",
            "-f",
            "qcow2",
            "-o",
            "cluster_size=2M",
            diskpath,
            size,
        ]

    def vm_prepare_disk_raw(self, diskpath: str, size: str) -> list[str]:
        return [
            "qemu-img",
            "create",
            "-q",
            "-f",
            "raw",
            diskpath,
            size,
        ]

    def _create_tpm_command(self, socketdir: str) -> list:
        return [
            "swtpm",
            "socket",
            "--tpm2",
            "--tpmstate",
            f"dir={socketdir}",
            "--ctrl",
            f"type=unixio,path={socketdir}-socket",
            "--log",
            "level=20",
        ]
