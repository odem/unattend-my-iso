#!/bin/bash

ISOFOLDER=data/iso
DISKFOLDER=data/disks
PIDFOLDER=data/pids
TPMFOLDER=data/tpm
ISONAME=
VMSSHPORT=5555
QCOWSIZE_DISK0=64
QCOWSIZE_DISK1=32
MEMSIZE=8192
CORES=4
UEFI_BOOT="yes"
CDROM_BOOT="yes"
ENABLE_LOGGING="no"
DEVICE_OUT1=enp6s0
ISOTYPE="debian12"
ID=0
export DEBIAN_FRONTEND=noninteractive

usage() {
    echo "Usage: $0 " 1>&2
    echo "      [-a <action>] [-n <isoname>]" 1>&2
    echo "      [-p <sshport>] [-s <disksize>]" 1>&2
    echo "      " 1>&2
    echo "      Action  : [wait,connect]" 1>&2
    echo "      Isoname : [isoname in ./iso without extension]" 1>&2
    echo "      Sshport : [ssh port (Default: 5555)]" 1>&2
    echo "      Disksize: [Size of disk in GB (Default: 128)]" 1>&2
}

while getopts ":a:e:h:n:p:s:U:C:D:t:" o; do
    case "$o" in
        a)
            ACTION=${OPTARG}
            ;;
        t)
            ISOTYPE=${OPTARG}
            ;;
        e)
            EXTRAPORTS=${OPTARG}
            ;;
        n)
            ISONAME=${OPTARG}
            ;;
        p)
            VMSSHPORT=${OPTARG}
            ;;
        s)
            QCOWSIZE_DISK0=${OPTARG}
            ;;
        h)
            usage && exit 0
            ;;
        U)
            UEFI_BOOT=${OPTARG}
            ;;
        C)
            CDROM_BOOT=${OPTARG}
            ;;
        D)
            DEVICE_OUT1=${OPTARG}
            ;;
        *)
            usage && exit 1
            ;;
    esac
done
shift $((OPTIND-1))



ID=0
[[ $ISOTYPE == "win11" ]] && ID="0a"
[[ $ISOTYPE == "guac" ]] && ID="0b"
[[ $ISOTYPE == "debian12" ]] && ID="0c"
[[ $ISOTYPE == "deb12qtile" ]] && ID="0d"
FORWARDS="$FORWARDS,hostfwd=tcp::2222-:22"

QCOWIMAGE_DISK0="$DISKFOLDER/$ISONAME-disk0".qcow2
DISKPATH_EFI="$DISKFOLDER/${ISONAME}_OVMF_VARS.fd"
PIDFILE="$PIDFOLDER/$ISONAME".pid
TPMSOCKET="tpm-$ISONAME"
DISKOPTIONS_DISK0="cache-size=16M,cache=none,file=$QCOWIMAGE_DISK0"
FORWARDS="hostfwd=tcp::$VMSSHPORT-:22" # ssh
if [[ $EXTRAPORTS -eq 1 ]] ; then
    FORWARDS="$FORWARDS,hostfwd=tcp::8006-:8006" # for proxmox webui
fi

kvminstall() {
    sudo -E apt --yes install qemu-kvm swtpm
}

vmdisk(){
    mkdir -p $DISKFOLDER
    if [[ ! -f "$QCOWIMAGE_DISK0" ]] ; then
        echo "Creating disk0 with: $QCOWSIZE_DISK0 GB"
        qemu-img create -q -f qcow2 -o cluster_size=2M "$QCOWIMAGE_DISK0" "$QCOWSIZE_DISK0"G
    else
        echo "Disk already exists"
    fi
}

vmstart() {
    echo "Starting VM: $QCOWIMAGE_DISK0"
    # Variable options
    UEFI_DRIVES=""
    if [ "$UEFI_BOOT" == "yes" ] ; then
        if [ ! -f "$DISKFOLDER/${ISONAME}_OVMF_VARS.fd" ] ; then
            rm -rf "$DISKPATH_EFI"
            cp /usr/share/OVMF/OVMF_VARS.fd "$DISKPATH_EFI"
        fi
        chmod 644 "$DISKPATH_EFI"
        UEFI_DRIVES="-drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE.fd \
            -drive if=pflash,format=raw,file=$DISKPATH_EFI"
    fi

    CDROM_DRIVES=""
    if [ "$CDROM_BOOT" == "yes" ] ; then
        CDROM_DRIVES="-cdrom $ISOFOLDER/$ISONAME.iso -boot order=cd"
    fi

    mkdir -p $TPMFOLDER
    SOCKET_FOLDER=$TPMFOLDER/$TPMSOCKET
    mkdir -p "$SOCKET_FOLDER"
    pkill -f dir="$TPMFOLDER/$TPMSOCKET"
    swtpm socket --tpm2 --tpmstate dir="$SOCKET_FOLDER" --ctrl type=unixio,path="$SOCKET_FOLDER-socket" --log level=20 >/dev/null 2>/dev/null &

    mkdir -p $PIDFOLDER
    INVOKE_CMD="sudo kvm \
        -enable-kvm  \
        -machine q35,kernel_irqchip=on,accel=kvm,usb=off,vmport=off,smm=on \
        -cpu host -smp $CORES,sockets=1,cores=$CORES,threads=1 -m $MEMSIZE \
        -parallel none -serial none -k de \
        -device virtio-balloon \
        -device usb-ehci -device usb-tablet \
        -pidfile $PIDFILE \
        -netdev user,id=mynet0,"$FORWARDS" \
        -device virtio-net-pci,netdev=mynet0 \
        -object rng-random,id=rng0,filename=/dev/urandom \
        -chardev socket,id=chrtpm,path=$SOCKET_FOLDER-socket \
        -tpmdev emulator,id=tpm0,chardev=chrtpm \
        -device tpm-tis,tpmdev=tpm0 \
        -device virtio-rng-pci,rng=rng0 \
        -object iothread,id=io0 \
        -drive if=none,id=disk0,format=qcow2,$DISKOPTIONS_DISK0 \
        -device virtio-blk-pci,drive=disk0,scsi=off,iothread=io0 \
        $UEFI_DRIVES $CDROM_DRIVES $LOG_OPTIONS"
    echo "Running VM: $ISONAME (CDROM: $CDROM_BOOT, UEFI: $UEFI_BOOT)"
    eval "$INVOKE_CMD" &
}

vmstop() {
    sudo ifconfig "$NICNAME" down
    sudo brctl delif brback "$NICNAME"
    if [ -f "$PIDFILE" ] ; then
        PID=$(sudo cat "$PIDFILE")
        sudo kill "$PID"
        sudo rm -rf "$PIDFILE"
    else
        echo "No pidfile: $PIDFILE"
    fi
    pkill -f dir="$TPMFOLDER/$TPMSOCKET"
    exit 0
}

case "$ACTION" in
    "install")
        kvminstall
        ;;
    "start")
        [[ -z "$ISONAME" ]] && echo "No Isoname specified" && usage && exit 1
        vmstart
        ;;
    "stop")
        [[ -z "$ISONAME" ]] && echo "No Isoname specified" && usage && exit 1
        vmstop
        ;;
    "disk")
        [[ -z "$ISONAME" ]] && echo "No Isoname specified" && usage && exit 1
        vmdisk
        ;;
     *)
        echo "Not a valid target: '$1'"
        ;;
esac


