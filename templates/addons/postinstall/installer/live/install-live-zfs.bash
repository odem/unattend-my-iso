#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -eo pipefail

# Read kernel or exit
KVERSION="$1"
echo "Kernel version was: '$KVERSION'"
[[ -n "$KVERSION" ]] || exit 1

# Install
apt update
echo "zfs-dkms zfs-dkms/license/accepted boolean true" | sudo debconf-set-selections
echo "zfs-dkms zfs-dkms/license/confirm boolean true" | sudo debconf-set-selections
apt install -y debootstrap parted gdisk dosfstools \
  zfsutils-linux zfs-dkms linux-headers-"$KVERSION"
