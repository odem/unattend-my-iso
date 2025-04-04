import os
import subprocess
from unattend_my_iso.common.config import TaskConfig, TemplateConfig
from unattend_my_iso.core.vm.hypervisor_base import HypervisorArgs, UmiHypervisorBase
from unattend_my_iso.common.logging import log_debug, log_error, log_info


class UmiHypervisorKvm(UmiHypervisorBase):
    def __init__(self) -> None:
        UmiHypervisorBase.__init__(self)

    def vm_run(self, args: TaskConfig, args_hv: HypervisorArgs) -> bool:
        log_info(f"Running VM: {args_hv.name}")
        runcmd = self._create_run_command(args, args_hv)
        if args.run.daemonize:
            proc = subprocess.Popen(
                runcmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            log_info(f"VMRUN was initiated: {proc.pid}")
        else:
            proc = subprocess.run(runcmd, capture_output=True, text=True)
            if proc.returncode != 0:
                log_error(f"VMRUN not successful: {proc.stdout} {proc.stderr}")
                return False
        return True

    def vm_get_args(self, args: TaskConfig, template: TemplateConfig) -> HypervisorArgs:
        cdrom = self.files._get_path_isofile(args)
        vmdir = self.files._get_path_vm(args)
        disk = f"{vmdir}/{args.run.diskname}"
        return HypervisorArgs(
            args.target.template,
            template.iso_type,
            args.run.uefi_boot,
            cdrom,
            [disk],
            args.run.net_devs,
            args.run.net_ports,
            args.run.res_cpu,
            args.run.res_mem,
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
        ret = subprocess.run(rmcmd, capture_output=True, text=True)
        if ret.returncode == 0:
            log_debug(f"Disk created with size {size_gb} GB -> {diskpath}")
            return True
        log_error(f"Error while creating disk size {size_gb} GB -> {diskpath}")
        return False

    def vm_prepare_tpm(self, socketdir: str, template: TemplateConfig) -> bool:
        if template.iso_type == "windows":
            if os.path.exists(f"{socketdir}-socket"):
                subprocess.run(["pkill", "-f", "swtpm"])
            os.makedirs(socketdir, exist_ok=True)
            runcmd = self._create_tpm_command(socketdir)
            log_debug(f"RUNCMD: {' '.join(runcmd)}")
            subprocess.Popen(
                runcmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            log_info("SWTPM was initiated")
        return True

    def _prepare_disk_efi(self, args: TaskConfig, efidisk: str) -> bool:
        if os.path.exists(efidisk) is False:
            rmcmd = ["rm", efidisk]
            cpcmd = ["cp", args.run.uefi_ovmf_vars, efidisk]
            # chmodcmd = ["chmod", "644", efidisk]
            subprocess.run(rmcmd, capture_output=True, text=True)
            copied = subprocess.run(cpcmd, capture_output=True, text=True)
            if copied.returncode != 0:
                log_error(
                    f"Could not copy ovmf efi disk: {args.run.uefi_ovmf_vars} to {efidisk}"
                )
                return False
            # subprocess.run(chmodcmd, capture_output=True, text=True)
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
        vmdir = f"{args.sys.path_vm}/{args.run.instname}"
        pidfile = f"{vmdir}/vm.pid"
        smpinfo = f"{args_hv.sys_cpu},sockets=1,cores={args_hv.sys_cpu},threads=1"
        machineinfo = "q35,kernel_irqchip=on,accel=kvm,usb=off,vmport=off,smm=on"
        command = ["qemu-system-x86_64"]
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
        vmdir = f"{args.sys.path_vm}/{args.run.instname}"
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

    def _create_net_args(self, args_hv: HypervisorArgs) -> list[str]:
        i = 0
        arr_netdevs = []
        if len(args_hv.netdevs) == 0:
            return []
        for dev in args_hv.netdevs:
            if dev != "" and dev.startswith("nat"):
                arr_fwd = []
                for el in args_hv.portfwd:
                    log_debug(f"EL: {el}")
                    arr_fwd += [f"hostfwd=tcp::{el[0]}-:{el[1]}"]
                userstr = f'user,{",".join(arr_fwd)}'
                arr_netdevs += ["-net", "nic,model=virtio", "-net", userstr]
            elif dev != "" and dev.startswith("tap"):
                netname = f"net{i}"
                devopt = f"e1000,netdev={netname}"
                scriptopts = "script=no,downscript=no"
                tapopt = f"tap,id={netname},ifname={dev},{scriptopts}"
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
                    driveopts = f"drive={diskid},scsi=off,iothread={ioname}"
                    diskopts = f"file={disk},format=qcow2,{diskcache}"
                    arr_disk += ["-object", f"iothread,id={ioname}"]
                    arr_disk += ["-drive", f"if=none,id={diskid},{diskopts}"]
                    arr_disk += ["-device", f"virtio-blk-pci,{driveopts}"]
                    i += 1
                else:
                    log_error(f"Invalid disk specified: '{disk}'")
        return arr_disk
