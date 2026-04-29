#!/bin/bash

KVERSION="$1"
echo "Kernel version was: '$KVERSION'"
[[ -z "$KVERSION" ]] && exit 1

/opt/umi/postinstall/installer/default/offline_packages.bash
/opt/umi/postinstall/installer/default/hostnames.bash
/opt/umi/postinstall/installer/default/hostnet_dhcp.bash
/opt/umi/postinstall/installer/default/apt.bash

apt install -y openssh-server
/usr/local/bin/install-user-live.bash

apt update
echo "zfs-dkms zfs-dkms/license/accepted boolean true" |
  sudo debconf-set-selections
apt install -y debootstrap parted gdisk dosfstools \
  zfsutils-linux zfs-dkms linux-headers-"$KVERSION"
dkms autoinstall
modprobe zfs
