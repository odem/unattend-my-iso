import os
from unattend_my_iso.core.subprocess.caller import run
from unattend_my_iso.common.config import TaskConfig
from unattend_my_iso.common.logging import log_debug, log_error
from unattend_my_iso.core.files.file_manager import UmiFileManager
from unattend_my_iso.core.vm.hypervisor_base import HypervisorArgs


class UmiQemuCommands:
    def __init__(self) -> None:
        self.files = UmiFileManager()

    def create_run_command(self, args: TaskConfig, args_hv: HypervisorArgs) -> list:
        command = self._create_invoke_args()
        command += self._create_cpu_args(args_hv)
        command += self._create_display_args(args, args_hv)
        command += self._create_pidfile_args(args)
        command += self._create_machine_args()
        command += self._create_memory_args(args_hv)
        command += self._create_usb_args()
        command += self._create_rng_args()
        command += self._create_legacy_args()
        command += self._create_uefi_args(args, args_hv)
        command += self._create_secureboot_args(args, args_hv)
        command += self._create_tpm_args(args, args_hv)
        command += self._create_net_args(args_hv)
        command += self._create_disk_args(args_hv)
        command += self._create_cdrom_args(args_hv)
        return command

    def _create_invoke_args(self) -> list[str]:
        return ["sudo", "qemu-system-x86_64"]

    def _create_cpu_args(self, args_hv: HypervisorArgs) -> list[str]:
        smpinfo = f"{args_hv.sys_cpu},sockets=1,cores={args_hv.sys_cpu},threads=1"
        return ["--enable-kvm", "-cpu", "host", "-smp", smpinfo]

    def _create_display_args(
        self, args: TaskConfig, args_hv: HypervisorArgs
    ) -> list[str]:
        display_args = []
        if args.run.spice_port > 0:
            display_args = [
                "-vga",
                "qxl",
                "-spice",
                f"port={args.run.spice_port},addr=127.0.0.1,disable-ticketing",
            ]
        return display_args

    def _create_pidfile_args(self, args: TaskConfig) -> list[str]:
        vmdir = f"{args.sys.path_vm}/{args.run.vmname}"
        pidfile = f"{vmdir}/{args.run.file_pid}"
        return ["-pidfile", pidfile]

    def _create_memory_args(self, args_hv: HypervisorArgs) -> list[str]:
        return ["-m", f"{args_hv.sys_mem}", "-device", "virtio-balloon"]

    def _create_machine_args(self) -> list[str]:
        return ["-machine", "q35,kernel_irqchip=on,accel=kvm,usb=off,vmport=off,smm=on"]

    def _create_usb_args(self) -> list[str]:
        return ["-device", "usb-ehci", "-device", "usb-tablet"]

    def _create_legacy_args(self) -> list[str]:
        return ["-parallel", "none", "-serial", "none", "-k", "de"]

    def _create_rng_args(self) -> list[str]:
        arr = ["-device", "virtio-rng-pci,rng=rng0"]
        arr += ["-object", "rng-random,id=rng0,filename=/dev/urandom"]
        return arr

    def _create_secureboot_args(
        self, args: TaskConfig, args_hv: HypervisorArgs
    ) -> list[str]:
        sb_args = []
        if args.run.secure_boot:
            sb_args = [
                "-global",
                "driver=cfi.pflash01,property=secure,value=on",
            ]
        return sb_args

    def _create_uefi_args(self, args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
        vmdir = f"{args.sys.path_vm}/{args.run.vmname}"
        uefi_vars = args.run.uefi_ovmf_vars
        uefi_code = args.run.uefi_ovmf_code
        if args.run.secure_boot:
            uefi_vars = args.run.uefi_ovmf_vars_ms
            uefi_code = args.run.uefi_ovmf_code_ms

        varsname = os.path.basename(uefi_vars)
        efidisk = f"{vmdir}/{varsname}"
        if args_hv.uefi is True:
            pflash = "if=pflash,format=raw"
            arr_uefi = ["-drive", f"{pflash},file={uefi_code},readonly=on"]
            arr_uefi += ["-drive", f"{pflash},file={efidisk}"]
            return arr_uefi
        return []

    def _create_tpm_args(self, args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
        arr_tpm = []
        vmdir = self.files._get_path_vm(args)
        socketdir = f"{vmdir}/swtpm-socket"
        if args_hv.vmtype == "windows":
            arr_tpm += [
                "-chardev",
                f"socket,id=chrtpm,path={socketdir}",
                "-tpmdev",
                "emulator,id=tpm0,chardev=chrtpm",
                "-device",
                "tpm-tis,tpmdev=tpm0",
            ]
        return arr_tpm

    def _create_net_args_nat(self, args_hv: HypervisorArgs) -> list[str]:
        arr_fwd = []
        for portlist in args_hv.portfwd:
            if len(portlist) > 1:
                arr_fwd += [f"hostfwd=tcp::{portlist[0]}-:{portlist[1]}"]
        userstr = f'user,{",".join(arr_fwd)}'
        return ["-net", "nic,model=virtio", "-net", userstr]

    def _create_net_args_tap(
        self, name: str, netindex: int, mac: str = ""
    ) -> list[str]:
        if mac == "":
            mac = self._generate_random_mac()
        netname = f"net{netindex}"
        devopt = f"e1000,netdev={netname},mac={mac}"
        scriptopts = "script=no,downscript=no"
        tapopt = f"tap,id={netname},ifname={name},{scriptopts}"
        return ["-netdev", tapopt, "-device", devopt]

    def _create_net_args(self, args_hv: HypervisorArgs) -> list[str]:
        i = 0
        arr_netdevs = []
        if len(args_hv.netdevs) == 0:
            return []
        for devargs in args_hv.netdevs:
            name = ""
            bridge = ""
            if len(devargs) > 0:
                name = devargs[0]
            if len(devargs) >= 2:
                name = devargs[0]
                bridge = devargs[1]
            if name != "" and bridge == "" and name.startswith("nat"):
                log_debug(
                    f"Using NAT device with ports: {args_hv.portfwd}",
                    self.__class__.__qualname__,
                )
                arr_netdevs += self._create_net_args_nat(args_hv)
            if name != "" and bridge != "":
                log_debug(
                    f"Using TAP device with bridge: {bridge}",
                    self.__class__.__qualname__,
                )
                arr_netdevs += self._create_net_args_tap(name, i)
                i += 1
        return arr_netdevs

    def _create_disk_args(self, args_hv: HypervisorArgs) -> list[str]:
        arr_disk = []
        if len(args_hv.disks) > 0:
            for i, disklist in enumerate(args_hv.disks):
                if isinstance(disklist, list) and len(disklist) >= 2:
                    arr_disk += self._create_disk_arg(i, disklist)
                else:
                    log_error(f"Unknown disk specification: {disklist}")
        return arr_disk

    def _create_disk_arg(self, diskindex: int, disklist: list) -> list[str]:
        arr_disk = []
        filename = disklist[0]
        disktype = "hdd"
        diskcache = "none"
        if len(disklist) >= 3:
            disktype = disklist[2]
        if len(disklist) >= 4:
            diskcache = disklist[3]
        if filename != "" and disktype == "hdd":
            arr_disk += self._create_disk_args_hdd(filename, diskindex, diskcache)
        elif filename != "" and disktype == "nvme":
            arr_disk += self._create_disk_args_nvme(filename, diskindex, diskcache)
        else:
            log_error(
                f"Invalid disk specified: '{disklist}'",
                self.__class__.__qualname__,
            )
        return arr_disk

    def _create_cdrom_args(self, args_hv: HypervisorArgs) -> list[str]:
        arr_cdrom = []
        if args_hv.cdrom != "":
            arr_cdrom += ["-cdrom", f"{args_hv.cdrom}", "-boot", "order=cd"]
        return arr_cdrom

    def _generate_random_mac(self) -> str:
        proc = run(["randmac"], capture_output=True, text=True, check=True)
        if proc is not None and proc.returncode == 0:
            mac = str(proc.stdout)
            mac = mac.replace("\n", "")
            log_debug(f"Random MAC generated: {mac}", self.__class__.__qualname__)
            return mac
        log_error("Got no random MAC")
        return ""

    def _create_disk_args_hdd(
        self, filename: str, diskindex: int, cache: str = ""
    ) -> list[str]:
        diskcache = "none"
        arr_disk = []
        if filename != "":
            ioname = f"io{diskindex}"
            diskid = f"disk{diskindex}"
            diskcache = f"cache-size=16M,cache={cache}"
            driveopts = f"drive={diskid},iothread={ioname}"
            diskopts = f"file={filename},format=qcow2,{diskcache}"
            arr_disk += ["-object", f"iothread,id={ioname}"]
            arr_disk += ["-drive", f"if=none,id={diskid},{diskopts}"]
            arr_disk += ["-device", f"virtio-blk-pci,{driveopts}"]
        return arr_disk

    def _create_disk_args_nvme(
        self, filename: str, diskindex: int, cache: str = "none"
    ) -> list[str]:
        arr_disk = []
        if filename != "":
            diskid = f"disk{diskindex}"
            diskcache = f"cache={cache}"
            driveopts = f"drive={diskid},serial=nvme{diskindex}"
            diskopts = f"file={filename},format=raw,{diskcache}"
            arr_disk += ["-drive", f"if=none,id={diskid},{diskopts}"]
            arr_disk += ["-device", f"nvme,{driveopts}"]
        return arr_disk
