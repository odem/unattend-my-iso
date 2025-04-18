import os
from unattend_my_iso.core.subprocess.caller import (
    run,
    run_background,
    CalledProcessError,
    Popen,
    PIPE,
    DEVNULL,
)
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.core.net.net_manager import UmiNetworkManager
from unattend_my_iso.core.vm.hypervisor_base import HypervisorArgs, UmiHypervisorBase
from unattend_my_iso.common.logging import log_debug, log_error, log_info


class UmiHypervisorKvm(UmiHypervisorBase):
    def __init__(self) -> None:
        UmiHypervisorBase.__init__(self)
        self.net = UmiNetworkManager()

    def vm_run(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        runcmd = self._create_run_command(args, args_hv)
        log_info(
            f"Running VM   : {args_hv.name} (Daemonize: {args.run.daemonize})",
            self.__class__.__qualname__,
        )
        if args.run.verbosity >= 4:
            log_debug(f"Run command  : {' '.join(runcmd)}", self.__class__.__qualname__)
        if self.net.net_start(args_hv) is False:
            log_error(
                "Networking   : Could not setup network", self.__class__.__qualname__
            )
            return False

        if args.run.daemonize:
            return self.vm_run_nonblocking(runcmd, args_hv)
        return self.vm_run_blocking(runcmd, args_hv)

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

    def vm_run_nonblocking(self, runcmd: list[str], args_hv: HypervisorArgs) -> bool:
        proc = run_background(
            runcmd,
            stdin=DEVNULL,
            stdout=DEVNULL,
            stderr=DEVNULL,
            close_fds=True,
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

    def vm_get_args(self, args: TaskConfig, template: TemplateConfig) -> HypervisorArgs:
        vmdir = self.files._get_path_vm(args)
        pidfile = self.files._get_path_vmpid(args)
        disks = []
        for disk in args.run.disks:
            disks.append(f"{vmdir}/{disk}")

        cdrom = ""
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
        )

    def vm_prepare_disks(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        for disk in args_hv.disks:
            if os.path.exists(disk) is False:
                if self.vm_prepare_disk(args, disk) is False:
                    return False
        return True

    def vm_prepare_disk(self, args: TaskConfig, diskpath: str) -> bool:
        vmdir = self.files._get_path_vm(args)
        size_gb = args.run.disksize
        os.makedirs(vmdir, exist_ok=True)
        rmcmd = [
            "qemu-img",
            "create",
            "-q",
            "-f",
            "qcow2",
            "-o",
            "cluster_size=2M",
            diskpath,
            f"{size_gb}G",
        ]
        ret = run(rmcmd, capture_output=True, text=True)
        if ret.returncode == 0:
            log_debug(
                f"Disk created with size {size_gb} GB -> {diskpath}",
                self.__class__.__qualname__,
            )
            return True
        log_error(
            f"Error while creating disk size {size_gb} GB -> {diskpath}",
            self.__class__.__qualname__,
        )
        return False

    def vm_prepare_tpm(self, socketdir: str, template: TemplateConfig) -> bool:
        if template.iso_type == "windows":
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

    def _prepare_disk_efi(self, args: TaskConfig, efidisk: str) -> bool:
        if os.path.exists(efidisk) is False:
            rmcmd = ["rm", efidisk]
            cpcmd = ["cp", args.run.uefi_ovmf_vars, efidisk]
            run(rmcmd, capture_output=True, text=True)
            copied = run(cpcmd, capture_output=True, text=True)
            if copied.returncode != 0:
                log_error(
                    f"Could not copy ovmf efi disk: {args.run.uefi_ovmf_vars} to {efidisk}",
                    self.__class__.__qualname__,
                )
                return False
        return True

    def _create_run_command(self, args: TaskConfig, args_hv: HypervisorArgs) -> list:
        cmd_static = self._create_static_run_command(args, args_hv)
        cmd_dyn = self._create_dynamic_run_command(args, args_hv)
        all = [*cmd_static, *cmd_dyn]
        return all

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

    def _create_static_run_command(
        self, args: TaskConfig, args_hv: HypervisorArgs
    ) -> list[str]:
        vmdir = f"{args.sys.path_vm}/{args.run.vmname}"
        pidfile = f"{vmdir}/{args.run.file_pid}"
        smpinfo = f"{args_hv.sys_cpu},sockets=1,cores={args_hv.sys_cpu},threads=1"
        machineinfo = "q35,kernel_irqchip=on,accel=kvm,usb=off,vmport=off,smm=on"
        command = ["sudo", "qemu-system-x86_64"]
        command += ["--enable-kvm", "-cpu", "host", "-smp", smpinfo]
        command += ["-pidfile", pidfile]
        command += ["-machine", machineinfo]
        command += ["-m", f"{args_hv.sys_mem}", "-device", "virtio-balloon"]
        command += ["-parallel", "none", "-serial", "none", "-k", "de"]
        command += ["-device", "usb-ehci", "-device", "usb-tablet"]
        command += ["-device", "virtio-rng-pci,rng=rng0"]
        command += ["-object", "rng-random,id=rng0,filename=/dev/urandom"]
        return command

    def _create_dynamic_run_command(
        self, args: TaskConfig, args_hv: HypervisorArgs
    ) -> list[str]:
        arr_uefi = self._create_uefi_args(args, args_hv)
        arr_tpm = self._create_tpm_args(args, args_hv)
        arr_net = self._create_net_args(args_hv)
        arr_disks = self._create_disk_args(args, args_hv)
        arr_cdrom = self._create_cdrom_args(args_hv)
        return [*arr_disks, *arr_net, *arr_cdrom, *arr_uefi, *arr_tpm]

    def _create_cdrom_args(self, args_hv: HypervisorArgs) -> list[str]:
        arr_cdrom = []
        if args_hv.cdrom != "":
            arr_cdrom += ["-cdrom", f"{args_hv.cdrom}", "-boot", "order=cd"]
        return arr_cdrom

    def _create_tpm_args(self, args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
        arr_cdrom = []
        vmdir = self.files._get_path_vm(args)
        socketdir = f"{vmdir}/swtpm-socket"
        if args_hv.vmtype == "windows":
            arr_cdrom += [
                "-chardev",
                f"socket,id=chrtpm,path={socketdir}",
                "-tpmdev",
                "emulator,id=tpm0,chardev=chrtpm",
                "-device",
                "tpm-tis,tpmdev=tpm0",
            ]
        return arr_cdrom

    def _create_uefi_args(self, args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
        vmdir = f"{args.sys.path_vm}/{args.run.vmname}"
        efidisk = f"{vmdir}/OVMF_VARS.fd"
        if args_hv.uefi is True:
            if self._prepare_disk_efi(args, efidisk):
                pflash = "if=pflash,format=raw"
                arr_uefi = [
                    "-drive",
                    f"{pflash},file={args.run.uefi_ovmf_code},readonly=on",
                ]
                arr_uefi += ["-drive", f"{pflash},file={efidisk}"]
                return arr_uefi
        return []

    def _generate_random_mac(self) -> str:
        proc = run(["randmac"], capture_output=True, text=True, check=True)
        if proc is not None and proc.returncode == 0:
            mac = str(proc.stdout)
            mac = mac.replace("\n", "")
            log_debug(f"Random MAC generated: {mac}", self.__class__.__qualname__)
            return mac
        log_error("Got no random MAC")
        return ""

    def _create_net_args(self, args_hv: HypervisorArgs) -> list[str]:
        i = 0
        arr_netdevs = []
        if len(args_hv.netdevs) == 0:
            return []
        for devargs in args_hv.netdevs:
            mac = self._generate_random_mac()
            if len(devargs) == 2:
                name = devargs[0]
                bridge = devargs[1]
                if bridge != "":
                    if name != "" and name.startswith("nat"):
                        arr_fwd = []
                        for portlist in args_hv.portfwd:
                            arr_fwd += [f"hostfwd=tcp::{portlist[0]}-:{portlist[1]}"]
                        userstr = f'user,{",".join(arr_fwd)}'
                        arr_netdevs += [
                            "-net",
                            f"nic,model=virtio,mac={mac}",
                            "-net",
                            userstr,
                        ]
                    elif name != "" and name.startswith("tap"):
                        netname = f"net{i}"
                        devopt = f"e1000,netdev={netname},mac={mac}"
                        scriptopts = "script=no,downscript=no"
                        tapopt = f"tap,id={netname},ifname={name},{scriptopts}"
                        arr_netdevs += ["-netdev", tapopt, "-device", devopt]
                        i += 1
        return arr_netdevs

    def _create_disk_args(self, args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
        arr_disk = []
        if len(args_hv.disks) > 0:
            i = 0
            for disk in args_hv.disks:
                if disk != "":
                    if os.path.exists(disk) is False:
                        self.vm_prepare_disk(args, disk)
                    ioname = f"io{i}"
                    diskid = f"disk{i}"
                    diskcache = "cache-size=16M,cache=none"
                    driveopts = f"drive={diskid},iothread={ioname}"
                    diskopts = f"file={disk},format=qcow2,{diskcache}"
                    arr_disk += ["-object", f"iothread,id={ioname}"]
                    arr_disk += ["-drive", f"if=none,id={diskid},{diskopts}"]
                    arr_disk += ["-device", f"virtio-blk-pci,{driveopts}"]
                    i += 1
                else:
                    log_error(
                        f"Invalid disk specified: '{disk}'", self.__class__.__qualname__
                    )
        return arr_disk
