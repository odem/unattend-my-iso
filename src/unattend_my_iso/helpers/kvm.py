import os
import subprocess
from dataclasses import dataclass
from unattend_my_iso.helpers.config import TaskConfig
from unattend_my_iso.helpers.logging import log_debug, log_error, log_info

DIR_OVMF_CODE = "/usr/share/OVMF/OVMF_CODE.fd"
DIR_OVMF_VARS = "/usr/share/OVMF/OVMF_VARS.fd"


@dataclass
class HypervisorArgs:
    name: str
    uefi: bool
    cdrom: str
    disks: list[str]
    netdevs: list[str]
    portfwd: list[tuple[int, int]]
    sys_cpu: int
    sys_mem: int


def run_vm(args: TaskConfig, args_hv: HypervisorArgs) -> bool:
    log_info(f"Running VM: {args_hv.name}")
    runcmd = _create_run_command(args, args_hv)
    proc = subprocess.Popen(runcmd)
    if proc.returncode == 0:
        log_info("VMRUN was initiated")
        return True
    log_error(f"Error on VMRUN: {proc.returncode}")
    return False


def _create_run_command(args: TaskConfig, args_hv: HypervisorArgs) -> list:
    cmd_static = _create_static_run_command(args, args_hv)
    cmd_dyn = _create_dynamic_run_command(args, args_hv)
    all = [*cmd_static, *cmd_dyn]
    return all


def _create_static_run_command(args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
    vmdir = f"{args.sys.vm_path}/{args.target.template}"
    pidfile = f"{vmdir}/vm.pid"
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


def _create_dynamic_run_command(args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
    arr_cdrom = _create_cdrom_args(args_hv)
    arr_uefi = _create_uefi_args(args, args_hv)
    arr_net = _create_net_args(args_hv)
    arr_disks = _create_disk_args(args_hv)
    return [*arr_disks, *arr_net, *arr_cdrom, *arr_uefi]


def _create_cdrom_args(args_hv: HypervisorArgs) -> list[str]:
    arr_cdrom = []
    if args_hv.cdrom != "":
        arr_cdrom += ["-cdrom", f"{args_hv.cdrom}", "-boot", "order=cd"]
    return arr_cdrom


def _create_uefi_args(args: TaskConfig, args_hv: HypervisorArgs) -> list[str]:
    vmdir = f"{args.sys.vm_path}/{args.target.template}"
    efidisk = f"{vmdir}/OVMF_VARS.fd"
    if args_hv.uefi is True:
        if prepare_efidisk(efidisk):
            pflash = "if=pflash,format=raw"
            arr_uefi = ["-drive", f"{pflash},file={DIR_OVMF_CODE},readonly=on"]
            arr_uefi += ["-drive", f"{pflash},file={efidisk}"]
            return arr_uefi
    log_error("Error creating uefi arguments")
    return []


def _create_net_args(args_hv: HypervisorArgs) -> list[str]:
    i = 0
    arr_netdevs = []
    if len(args_hv.netdevs) == 0:
        return []
    for dev in args_hv.netdevs:
        if dev != "" and dev.startswith("nat"):
            arr_fwd = []
            for el in args_hv.portfwd:
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


def _create_disk_args(args_hv: HypervisorArgs) -> list[str]:
    arr_disk = []
    if len(args_hv.disks) > 0:
        i = 0
        for disk in args_hv.disks:
            if disk != "" and os.path.exists(disk):
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


def prepare_qcowdisk(diskpath: str, size_gb: int) -> bool:
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


def prepare_efidisk(efidisk: str) -> bool:
    rmcmd = ["sudo", "rm", efidisk]
    cpcmd = ["sudo", "cp", DIR_OVMF_VARS, efidisk]
    rmcmd = ["sudo", "chmod", "644", efidisk]
    subprocess.run(rmcmd, capture_output=True, text=True)
    copied = subprocess.run(cpcmd, capture_output=True, text=True)
    if copied.returncode != 0:
        log_error("Could not copy ovmf efi disk")
        return False
    subprocess.run(rmcmd, capture_output=True, text=True)
    return True
