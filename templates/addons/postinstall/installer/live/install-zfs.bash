#!/usr/bin/env bash
set -euo pipefail

echo "[0/7] Config..."

# -----------------------
# POOLS
# -----------------------

RPOOL=(
  "rpool"
  "mirror"
  "/dev/disk/by-id/virtio-DISK-0 /dev/disk/by-id/virtio-DISK-1"
)

TANK=(
  "tank"
  "mirror"
  "/dev/disk/by-id/virtio-DISK-2 /dev/disk/by-id/virtio-DISK-3"
)

# -----------------------
# HELPERS
# -----------------------
export DEBIAN_FRONTEND=noninteractive
echo "zfs-dkms zfs-dkms/license/accepted boolean true" | debconf-set-selections

apt update
apt install -y debootstrap parted gdisk dosfstools \
  zfsutils-linux zfs-dkms linux-headers-"$(uname -r)"
dkms autoinstall
modprobe zfs

get_part() {
  echo "${1}-part${2}"
}

disk_in_list() {
  local disk="$1"
  shift
  for d in "$@"; do
    [[ "$d" == "$disk" ]] && return 0
  done
  return 1
}

# -----------------------
# PARTITIONING (RPOOL DEFINES LAYOUT)
# -----------------------

read -r -a RPOOL_DISKS <<<"${RPOOL[2]}"

partition_disk() {
  local d="$1"

  echo "-> $d"

  sgdisk --zap-all "$d"
  wipefs -a "$d" || true
  sgdisk -o "$d"

  if disk_in_list "$d" "${RPOOL_DISKS[@]}"; then
    echo "   system disk (EFI + bpool + rpool)"

    sgdisk -n1:1M:+512M -t1:EF00 "$d" # EFI
    sgdisk -n2:0:+1G -t2:BF01 "$d"    # bpool (/boot)
    sgdisk -n3:0:0 -t3:BF00 "$d"      # rpool

  else
    echo "   data disk"

    sgdisk -n1:1M:0 -t1:BF00 "$d"
  fi
}

partition_all() {
  echo "[Partitioning...]"

  ALL_DISKS=("${RPOOL_DISKS[@]}")

  read -r -a TANK_DISKS <<<"${TANK[2]}"
  ALL_DISKS+=("${TANK_DISKS[@]}")

  ALL_DISKS=($(printf "%s\n" "${ALL_DISKS[@]}" | sort -u))

  for d in "${ALL_DISKS[@]}"; do
    partition_disk "$d"
  done

  partprobe
  udevadm settle --timeout=30
}

# -----------------------
# EFI FORMAT
# -----------------------

format_efi() {
  echo "[EFI formatting...]"

  for d in "${RPOOL_DISKS[@]}"; do
    mkfs.vfat -F32 -n EFI "$(get_part "$d" 1)"
  done
}

# -----------------------
# ZFS OPTIONS
# -----------------------

ZPOOL_OPTS="-f -o ashift=12 -o autotrim=on"
ZFS_PROPS="-O acltype=posixacl -O xattr=sa -O relatime=on -O normalization=formD -O mountpoint=none"

# -----------------------
# POOL BUILDERS
# -----------------------

create_bpool() {
  local name="${RPOOL[0]}"
  local mode="${RPOOL[1]}"

  devs=()
  for d in "${RPOOL_DISKS[@]}"; do
    devs+=("$(get_part "$d" 2)")
  done

  echo "Creating bpool"

  zpool create \
    $ZPOOL_OPTS \
    -o compatibility=grub2 \
    $ZFS_PROPS \
    "$name" "$mode" "${devs[@]}"
}

build_data_devs() {
  local -n pool=$1

  read -r -a disks <<<"${pool[2]}"

  devs=()

  for d in "${disks[@]}"; do
    if disk_in_list "$d" "${RPOOL_DISKS[@]}"; then
      devs+=("$(get_part "$d" 3)")
    else
      devs+=("$(get_part "$d" 1)")
    fi
  done
}

create_rpool() {
  build_data_devs RPOOL

  echo "Creating rpool"

  zpool create \
    $ZPOOL_OPTS \
    $ZFS_PROPS \
    -O compression=lz4 \
    "${RPOOL[0]}" "${RPOOL[1]}" "${devs[@]}"
}

create_tank() {
  [[ -z "${TANK[0]}" ]] && return 0

  build_data_devs TANK

  echo "Creating tank"

  zpool create \
    $ZPOOL_OPTS \
    $ZFS_PROPS \
    -O compression=lz4 \
    "${TANK[0]}" "${TANK[1]}" "${devs[@]}"
}

# -----------------------
# EXECUTION
# -----------------------

echo "[1/7] Partition disks..."
partition_all

echo "[2/7] Format EFI..."
format_efi

echo "[3/7] bpool..."
create_bpool

echo "[4/7] rpool..."
create_rpool

echo "[5/7] tank..."
create_tank

echo "[DONE]"
