import os
from unattend_my_iso.core.subprocess.caller import run
from unattend_my_iso.common.config import TaskConfig
from unattend_my_iso.common.logging import log_debug, log_error
from unattend_my_iso.core.files.file_manager import UmiFileManager
from unattend_my_iso.core.vm.hypervisor_base import HypervisorArgs


class UmiQemuCommands:
    def __init__(self) -> None:
        self.files = UmiFileManager()
        self.extender = "\\\n    "

    def bashformat(self, args: TaskConfig, cmd: list) -> list:
        if args.run.generate_run_script:
            if len(cmd) > 0:
                cmd.append(self.extender)
                if cmd is not None:
                    return cmd
        return cmd

    def create_run_command(self, args: TaskConfig, args_hv: HypervisorArgs) -> list:
        command = self._create_invoke_args(args)
        command += self._create_monitor_args(args, args_hv)
        command += self._create_log_args(args, args_hv)
        command += self._create_cpu_args(args, args_hv)
        command += self._create_display_args(args, args_hv)
        command += self._create_pidfile_args(args)
        command += self._create_machine_args(args)
        command += self._create_memory_args(args, args_hv)
        command += self._create_usb_args(args)
        command += self._create_rng_args(args)
        command += self._create_legacy_args(args)
        command += self._create_uefi_args(args, args_hv)
        command += self._create_secureboot_args(args, args_hv)
        command += self._create_tpm_args(args, args_hv)
        command += self._create_net_args(args, args_hv)
        command += self._create_disk_args(args, args_hv)
        command += self._create_cdrom_args(args, args_hv)
        command.pop()
        return command

    def _create_invoke_args(self, args: TaskConfig) -> list[str]:
        generated = ["sudo", "qemu-system-x86_64"]
        return self.bashformat(args, generated)

    def _create_monitor_args(
        self, args: TaskConfig, args_hv: HypervisorArgs
    ) -> list[str]:
        generated = []
        if args.run.enable_monitor_socket:
            generated = ["-monitor", "unix:qemu-monitor-socket,server,nowait"]
        return self.bashformat(args, generated)

    def _create_log_args(self, args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
        vmdir = self.files._get_path_vm(args)
        log_name = "qemu.log"
        full_name = f"{vmdir}/{log_name}"
        # if os.path.exists(full_name) is False:
        #     self.files.append_to_file(full_name, "")
        generated = []
        if args.run.enable_monitor_socket:
            generated = [
                "-d",
                "op,exec,int,cpu,fpu,mmu,pcall,cpu_reset,unimp,strace,tid",
                "-D",
                full_name,
            ]
        return self.bashformat(args, generated)

    def _create_cpu_args(self, args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
        cpuflags = "host"
        smpinfo = f"{args_hv.sys_cpu},sockets=1,cores={args_hv.sys_cpu},threads=1"
        if args_hv.vmtype in ["win", "windows"]:
            cpuflags = "host,hv_relaxed,hv_spinlocks=0x1fff,hv_vapic,hv_time"
        generated = ["-cpu", cpuflags, "-smp", smpinfo, "--enable-kvm"]
        return self.bashformat(args, generated)

    def _create_display_args(
        self, args: TaskConfig, args_hv: HypervisorArgs
    ) -> list[str]:
        generated = []
        if args.run.spice_port > 0:
            generated = [
                "-vga",
                "qxl",
                "-spice",
                f"port={args.run.spice_port},addr=127.0.0.1,disable-ticketing",
                "-device",
                "virtio-serial-pci",
                "-device",
                "virtserialport,chardev=spicechannel0,name=com.redhat.spice.0",
                "-chardev",
                "spicevmc,id=spicechannel0,name=vdagent",
                "-device",
                "virtserialport,chardev=charchannel1,id=channel1,name=org.spice-space.webdav.0",
                "-chardev",
                "spiceport,name=org.spice-space.webdav.0,id=charchannel1",
            ]
        return self.bashformat(args, generated)

    def _create_pidfile_args(self, args: TaskConfig) -> list[str]:
        vmdir = f"{args.sys.path_vm}/{args.run.vmname}"
        pidfile = f"{vmdir}/{args.run.file_pid}"
        generated = ["-pidfile", pidfile]
        return self.bashformat(args, generated)

    def _create_memory_args(
        self, args: TaskConfig, args_hv: HypervisorArgs
    ) -> list[str]:
        generated = ["-m", f"{args_hv.sys_mem}", "-device", "virtio-balloon"]
        return self.bashformat(args, generated)

    def _create_machine_args(self, args: TaskConfig) -> list[str]:
        generated = [
            "-machine",
            "q35,kernel_irqchip=on,accel=kvm,usb=off,vmport=off,smm=on",
        ]
        return self.bashformat(args, generated)

    def _create_usb_args(self, args: TaskConfig) -> list[str]:
        generated = ["-usb", "-device", "usb-ehci", "-device", "usb-tablet"]
        return self.bashformat(args, generated)

    def _create_legacy_args(self, args: TaskConfig) -> list[str]:
        generated = ["-parallel", "none", "-serial", "none", "-k", "de"]
        return self.bashformat(args, generated)

    def _create_rng_args(self, args: TaskConfig) -> list[str]:
        generated = ["-device", "virtio-rng-pci,rng=rng0"]
        generated += ["-object", "rng-random,id=rng0,filename=/dev/urandom"]
        return self.bashformat(args, generated)

    def _create_secureboot_args(
        self, args: TaskConfig, args_hv: HypervisorArgs
    ) -> list[str]:
        generated = []
        if args.run.secure_boot:
            generated = [
                "-global",
                "driver=cfi.pflash01,property=secure,value=on",
            ]
        return self.bashformat(args, generated)

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
            generated = self.bashformat(
                args, ["-drive", f"{pflash},file={uefi_code},readonly=on"]
            )
            generated += ["-drive", f"{pflash},file={efidisk}"]
            return self.bashformat(args, generated)
        return []

    def _create_tpm_args(self, args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
        generated = []
        vmdir = self.files._get_path_vm(args)
        socketdir = f"{vmdir}/swtpm-socket"
        if args_hv.vmtype == "windows":
            generated += self.bashformat(
                args, ["-chardev", f"socket,id=chrtpm,path={socketdir}"]
            )
            generated += self.bashformat(
                args, ["-tpmdev", "emulator,id=tpm0,chardev=chrtpm"]
            )
            generated += ["-device", "tpm-tis,tpmdev=tpm0"]
        return self.bashformat(args, generated)

    def _create_net_args_nat(
        self, args: TaskConfig, args_hv: HypervisorArgs
    ) -> list[str]:
        arr_fwd = []
        for portlist in args_hv.portfwd:
            if len(portlist) > 1:
                arr_fwd += [f"hostfwd=tcp::{portlist[0]}-:{portlist[1]}"]
        userstr = f'user,{",".join(arr_fwd)}'
        generated = ["-net", "nic,model=virtio", "-net", userstr]
        return generated

    def _create_net_args_tap(
        self, args: TaskConfig, name: str, netindex: int, mac: str = ""
    ) -> list[str]:
        if mac == "":
            mac = self._generate_random_mac()
        netname = f"net{netindex}"
        devopt = f"e1000,netdev={netname},mac={mac}"
        scriptopts = "script=no,downscript=no"
        tapopt = f"tap,id={netname},ifname={name},{scriptopts}"
        generated = ["-netdev", tapopt, "-device", devopt]
        return generated

    def _create_net_args(self, args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
        i = 0
        generated = []
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
                generated += self._create_net_args_nat(args, args_hv)
            if name != "" and bridge != "":
                log_debug(
                    f"Using TAP device with bridge: {bridge}",
                    self.__class__.__qualname__,
                )
                generated += self._create_net_args_tap(args, name, i)
                i += 1
        return self.bashformat(args, generated)

    def _create_disk_args(self, args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
        generated = []
        if len(args_hv.disks) > 0:
            for i, disklist in enumerate(args_hv.disks):
                if isinstance(disklist, list) and len(disklist) >= 2:
                    generated += self._create_disk_arg(args, i, disklist)
                else:
                    log_error(f"Unknown disk specification: {disklist}")
        return self.bashformat(args, generated)

    def _create_disk_arg(
        self, args: TaskConfig, diskindex: int, disklist: list
    ) -> list[str]:
        generated = []
        filename = disklist[0]
        disktype = "hdd"
        diskcache = "none"
        if len(disklist) >= 3:
            disktype = disklist[2]
        if len(disklist) >= 4:
            diskcache = disklist[3]
        if filename != "" and disktype == "hdd":
            generated += self._create_disk_args_hdd(
                args, filename, diskindex, diskcache
            )
        elif filename != "" and disktype == "nvme":
            generated += self._create_disk_args_nvme(
                args, filename, diskindex, diskcache
            )
        else:
            log_error(
                f"Invalid disk specified: '{disklist}'",
                self.__class__.__qualname__,
            )
        return generated

    def _create_cdrom_args(
        self, args: TaskConfig, args_hv: HypervisorArgs
    ) -> list[str]:
        generated = []
        if args_hv.cdrom != "":
            generated += ["-cdrom", f"{args_hv.cdrom}", "-boot", "order=cd"]
        return self.bashformat(args, generated)

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
        self, args: TaskConfig, filename: str, diskindex: int, cache: str = ""
    ) -> list[str]:
        diskcache = "none"
        generated = []
        if filename != "":
            ioname = f"io{diskindex}"
            diskid = f"disk{diskindex}"
            diskcache = f"cache-size=16M,cache={cache}"
            driveopts = f"drive={diskid},iothread={ioname}"
            diskopts = f"file={filename},format=qcow2,{diskcache}"
            generated += self.bashformat(args, ["-object", f"iothread,id={ioname}"])
            generated += self.bashformat(
                args, ["-drive", f"if=none,id={diskid},{diskopts}"]
            )
            generated += ["-device", f"virtio-blk-pci,{driveopts}"]
        return generated

    def _create_disk_args_nvme(
        self, args: TaskConfig, filename: str, diskindex: int, cache: str = "none"
    ) -> list[str]:
        generated = []
        if filename != "":
            diskid = f"disk{diskindex}"
            diskcache = f"cache={cache}"
            driveopts = f"drive={diskid},serial=nvme{diskindex}"
            diskopts = f"file={filename},format=raw,{diskcache}"
            generated += self.bashformat(
                args, ["-drive", f"if=none,id={diskid},{diskopts}"]
            )
            generated += ["-device", f"nvme,{driveopts}"]
        return generated
