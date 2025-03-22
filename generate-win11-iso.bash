#!/bin/bash

# Default config
VOLNAME=Win11
INCFOLDER=cfg/win11
OUTFOLDER=out
DISKFOLDER=disks
ISOFOLDER=iso
ISONAME=Win11_24H2_German_x64
ISONAME_VIO=virtio-win-0.1.229
OUTNAME=win11-custom
INFOLDER=$OUTFOLDER/$ISONAME
OUTFILE=$OUTFOLDER/${OUTNAME}
VIRTIOFOLDER=$OUTFOLDER/${ISONAME_VIO}
URL_VIRTIO="https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/archive-virtio/virtio-win-0.1.229-1/virtio-win-0.1.229.iso"
USERNAME=root
ROOTPASS=root
QCOWIMAGE_DISK0="$DISKFOLDER/$OUTNAME-disk0".qcow2
DISKPATH_EFI="$DISKFOLDER/${OUTNAME}_OVMF_VARS.fd"
export DEBIAN_FRONTEND=noninteractive

# Help
usage() {
    echo "Usage: $0 " 1>&2
    echo "      [-a <action>] [-n <isoname>]" 1>&2
    echo "      [-u <username>] [-p <userpass>]" 1>&2
    echo "      [-d <outdir>] [-i <incdir>]" 1>&2
    echo "      " 1>&2
    echo "      Action  : [clean,install,download,generate]" 1>&2
    echo "      Isoname : [isoname in ./iso without extension]" 1>&2
    echo "      Username: [Hostname to connect to (Default: localhost)]" 1>&2
    echo "      Userpass: [User name (Default: root)]" 1>&2
    echo "      Outdir  : [Output folder (Default: ./out)]" 1>&2
    echo "      IncDir  : [Include folder (Default: ./config)]" 1>&2
}

# install
toolinstall(){
    sudo -E apt --yes install rsync unzip unrar isolinux swtpm wimtools 1>&2 2>/dev/null
}
# clean
clean(){
    sudo umount "$MNTFOLDER" 1>&2 2>/dev/null
    rm -rf "$INFOLDER" "$MNTFOLDER" "$VIRTIOFOLDER"
    sudo rm -rf "$MODFOLDER"
    sudo rm -rf "$QCOWIMAGE_DISK0"
    sudo rm -rf "$DISKPATH_EFI"
}

# Download
download() {
    mkdir -p "$ISOFOLDER"
    if [ ! -f "$ISOFILE" ] ; then
        echo "No ISO file"
        exit 1
    fi
    if [ ! -f "$ISOFILE_VIO" ] ; then
        wget -O "$ISOFILE_VIO" "$URL_VIRTIO"
    fi
}
download_tools() {
    echo "Nothing to do"
}

# Mount and extract
copybase(){
    mkdir -p "$MNTFOLDER" "$INFOLDER"
    sudo mount "$ISOFILE" "$MNTFOLDER"
    echo "Mounting $MNTFOLDER to $INFOLDER"
    rsync -a -H --info=progress2 --exclude=TRANS.TBL "$MNTFOLDER"/ "$INFOLDER"
    chmod 755 -R "$INFOLDER"
    sudo umount "$MNTFOLDER"
    echo "ISO (OS Installer) copied"

    sudo mount "$ISOFILE_VIO" "$MNTFOLDER"
    echo "Mounted"
    rsync -a -H --info=progress2 --exclude=TRANS.TBL "$MNTFOLDER"/ "$VIRTIOFOLDER"
    chmod 755 -R "$VIRTIOFOLDER"
    sudo umount "$MNTFOLDER"
    sudo rm -rf "$MNTFOLDER"
    echo "ISO (virtio) copied"
}

# Ensure ssh key
ensurekey(){
    if [[ ! -f "$INCFOLDER"/ssh/id_rsa.pub ]] ; then
        mkdir -p "$INCFOLDER"/ssh
        if [[ -r /root/.ssh/id_rsa ]] ; then
            cp /root/.ssh/id_rsa* "$INCFOLDER"/ssh
        else
            ssh-keygen -t rsa -N '' -f "$INCFOLDER"/ssh/id_rsa
        fi
    fi
}

# Copy addons
copyaddons(){
    ensurekey
    mkdir -p "$INFOLDER"/postinstall/
    cp -r "$INCFOLDER"/ssh -t "$INFOLDER"/postinstall/
    cp -r "$INCFOLDER"/postinstall/*.* -t "$INFOLDER"/postinstall/
    cp -r "$INCFOLDER"/autounattend.xml "$INFOLDER"/autounattend.xml
    cp -r "$VIRTIOFOLDER" "$INFOLDER"/virtio
}

updateuser() {
    sed "s#<Name>user</Name>#<Name>$USERNAME</Name>#g" \
         -i "$INFOLDER/autounattend.xml"
    sed "s#<Username>user</Username>#<Username>$USERNAME</Username>#g" \
         -i "$INFOLDER/autounattend.xml"
    sed "s#<UserName>user</UserName>#<UserName>$USERNAME</UserName>#g" \
         -i "$INFOLDER/autounattend.xml"
    sed "s#<FullName>user</FullName>#<FullName>$USERNAME</FullName>#g" \
         -i "$INFOLDER/autounattend.xml"
    sed "s#<DisplayName>user</DisplayName>#<DisplayName>$USERNAME</DisplayName>#g" \
         -i "$INFOLDER/autounattend.xml"
    sed "s#<RegisteredOwner>user</RegisteredOwner>#<RegisteredOwner>$USERNAME</RegisteredOwner>#g" \
         -i "$INFOLDER/autounattend.xml"
    sed "s#<Value>user</Value>#<Value>$ROOTPASS</Value>#g" \
         -i "$INFOLDER/autounattend.xml"
    sed "s#C:\\\\Users\\\\root\\\\#C:\\\\Users\\\\$USERNAME\\\\#g" \
         -i "$INFOLDER/postinstall/postinstall.bat"
}

# Generate iso
geniso(){
    mkdir -p "$OUTFOLDER"

    # Create efi disk
    mkdir -p "$MNTFOLDER" "$INFOLDER"
    sudo mount "$ISOFILE" "$MNTFOLDER"
    dd if=/dev/zero of=out/efiboot.img bs=1M count=64
    sudo mkfs.fat -F32 out/efiboot.img
    mkdir -p out/efiboot/
    sudo mount -o loop out/efiboot.img out/efiboot

    sudo mkdir -p out/efiboot/efi/boot
    sudo wimlib-imagex extract "$MNTFOLDER"/sources/boot.wim 2 \
        "Windows/Boot/EFI/bootmgfw.efi" \
        --dest-dir=out/efiboot/efi/boot/
    echo "Extracted"
    sudo mv out/efiboot/efi/boot/bootmgfw.efi out/efiboot/efi/boot/bootx64.efi
    echo "Copied"
    sudo umount out/efiboot
    sudo umount "$MNTFOLDER"
    cp out/efiboot.img "$INFOLDER"
    rm -rf efiboot
    rm -rf mnt


xorriso -as mkisofs \
    -iso-level 3 \
    -full-iso9660-filenames \
    -volid "$VOLNAME" \
    -eltorito-boot boot/etfsboot.com \
    -eltorito-catalog boot/boot.cat \
    -no-emul-boot \
    -boot-load-size 8 \
    -boot-info-table \
    -eltorito-alt-boot \
    -e efiboot.img \
    -no-emul-boot \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -isohybrid-gpt-basdat \
    -o "$OUTFILE".iso \
    "$INFOLDER"
    echo "ISO created -> CFG: $INCFOLDER, IN: $INFOLDER, OUT: $OUTFILE"

}

# Read params
while getopts ":a:u:p:d:i:n:" o; do
    echo "Opt: $o -> $OPTARG"
    case "$o" in
        a)
            ACTION=${OPTARG}
            ;;
        u)
            USERNAME=${OPTARG}
            ;;
        p)
            ROOTPASS=${OPTARG}
            ;;
        d)
            OUTFOLDER=${OPTARG}
            ;;
        i)
            INCFOLDER=${OPTARG}
            ;;
        n)
            OUTNAME=${OPTARG}
            ;;
        *)
            ;;
    esac
done
shift $((OPTIND-1))

# Dynamic vars
MNTFOLDER=$OUTFOLDER/mnt
MODFOLDER=$OUTFOLDER/irmod
INFOLDER=$OUTFOLDER/$ISONAME
VIRTIOFOLDER=$OUTFOLDER/${ISONAME_VIO}
ISOFILE=$ISOFOLDER/${ISONAME}.iso
ISOFILE_VIO=$ISOFOLDER/${ISONAME_VIO}.iso
OUTFILE=$ISOFOLDER/${OUTNAME}

# Execute action
case "$ACTION" in
    "clean")
        [[ -z "$ISONAME" ]] && echo "No Isoname specified" && usage && exit 1
        clean
        ;;
    "install")
        [[ -z "$ISONAME" ]] && echo "No Isoname specified" && usage && exit 1
        toolinstall
        ;;
    "download")
        [[ -z "$ISONAME" ]] && echo "No Isoname specified" && usage && exit 1
        download
        download_tools
        ;;
    "generate")
        [[ -z "$ISONAME" ]] && echo "No Isoname specified" && usage && exit 1
        clean
        download
        download_tools
        copybase
        copyaddons
        updateuser
        echo "Generate ISO now......"
        geniso
        ;;
    *)
        echo "Not a valid target: '$1'"
        ;;
esac
