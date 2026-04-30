#!/bin/bash

# shellcheck disable=SC1090,1091

# -- Defaults
BPOOL_PARTS=()
RPOOL_PARTS=()
OPOOL_PARTS=()
declare -A DATASET_LB
# declare -A DATASET_MP
declare -a PROPS_GRUB=()
declare -a PROPS_POOL=()
declare -a PROPS_ZFS=()

DEBUG_ERASE_POOLS=1

# -- Globals ---
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive


# -- Errors ---
CONST_ERR_DISK=100
CONST_ERR_FORMAT=101

# -- ZFS Pool config ---
CFG_ZFS_NAME="debian"
CFG_ZFS_BPOOL=("bpool" "mirror")
CFG_ZFS_RPOOL=("rpool" "mirror")
CFG_ZFS_OPOOL=("opool" "mirror")
CFG_ZFS_DISKS_MAIN=(
  "/dev/disk/by-id/virtio-DISK-0"
  "/dev/disk/by-id/virtio-DISK-1"
)
CFG_ZFS_DISKS_OPTIONAL=(
  "/dev/disk/by-id/virtio-DISK-2"
  "/dev/disk/by-id/virtio-DISK-3"
)
CFG_ZFS_DATASETS=( 
  "'root', '/', 'rpool/ROOT/root-$CFG_ZFS_NAME'" 
  "'boot', '/boot', 'bpool/BOOT/boot-$CFG_ZFS_NAME'"
  "'home', '/home', 'rpool/ROOT/home-$CFG_ZFS_NAME'"
  "'data', '/srv', 'opool/OPTS/data-$CFG_ZFS_NAME'"
)
CFG_ZFS_PROPS_POOL=(
  "ashift=12"
  "autotrim=on"
)
CFG_ZFS_PROPS_ZFS=(
  "acltype=posixacl"
  "xattr=sa"
  "relatime=on"
  "normalization=formD"
  "mountpoint=none"
)
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

create_property_arrays() {
  PROPS_GRUB=("-o" "compatibility=grub2")
  for p in "${CFG_ZFS_PROPS_POOL[@]}"; do
    PROPS_POOL+=("-o")
    PROPS_POOL+=("$p")
  done
  for p in "${CFG_ZFS_PROPS_ZFS[@]}"; do
    PROPS_ZFS+=("-O")
    PROPS_ZFS+=("$p")
  done
}
create_disk_arrays() {
  read -r -a BPOOL_DISKS <<<"${CFG_ZFS_DISKS_MAIN[@]}"
  read -r -a RPOOL_DISKS <<<"${CFG_ZFS_DISKS_MAIN[@]}"
  read -r -a OPOOL_DISKS <<<"${CFG_ZFS_DISKS_OPTIONAL[@]}"
}
create_partition_arrays() {
  for d in "${BPOOL_DISKS[@]}"; do
    BPOOL_PARTS+=("${d}-part2")
  done
  for d in "${RPOOL_DISKS[@]}"; do
    RPOOL_PARTS+=("${d}-part3")
  done
  for d in "${OPOOL_DISKS[@]}"; do
    OPOOL_PARTS+=("${d}-part1")
  done
}
create_dataset_arrays() {
  for entry in "${CFG_ZFS_DATASETS[@]}"; do
    entry=${entry//\'/}
    IFS=',' read -r name mountpoint label<<< "$entry"
    name=${name// /}
    mountpoint=${mountpoint// /}
    label=${label// /}
    DATASET_LB["$name"]=$label
    # DATASET_MP["$name"]=$mountpoint
  done
}
destroy_pools() {
  if [[ $DEBUG_ERASE_POOLS -eq 1 ]]; then
    set +euo pipefail
    CHECK_ZPOOL=$(which zpool)
    if [[ "$CHECK_ZPOOL" != "" ]] ; then
      zpool destroy bpool
      zpool destroy rpool
      zpool destroy opool
    else
      echo "Could not detroy pools. zpool not available!"
    fi
    set -euo pipefail
  fi
}
sync_disks() {
  partprobe >/dev/null 2>&1
  udevadm trigger
  udevadm settle
  sync
}
assert_disk() {
  local disk="$1"
  if [[ ! -e "$1" ]]; then
    echo "-> ERROR   :  $disk not found in /dev/disk/by-id/"
    exit $CONST_ERR_DISK
  else
    echo "-> SUCCESS :  $disk "
  fi
}

install_essentials() {
  apt update
  echo "zfs-dkms zfs-dkms/license/accepted boolean true" \
    | sudo debconf-set-selections
  apt install -y debootstrap parted gdisk dosfstools \
    zfsutils-linux zfs-dkms linux-headers-"$(uname -r)"
  dkms autoinstall
  modprobe zfs
}
wipe_disk() {
  local disk="$1"
  if [[ -e "$disk" ]]; then
    if sgdisk --zap-all "$disk" >/dev/null; then
      if wipefs -a "$disk" >/dev/null; then
        echo "-> SUCCESS :  Wiped disk $disk"
      else
        echo "-> ERROR   :  Wiping failed for $disk"
      fi
    else
      echo "-> ERROR   :  Zapping failed for $disk"
    fi
  else
    echo "-> ERROR   :  Disk not found: $disk"
  fi
}
disks_check() {
  echo "Checking bpool disks:"
  for d in "${BPOOL_DISKS[@]}"; do
    assert_disk "$d"
  done
  echo "Checking rpool disks:"
  for d in "${RPOOL_DISKS[@]}"; do
    assert_disk "$d"
  done
  echo "Checking opool disks:"
  for d in "${OPOOL_DISKS[@]}"; do
    assert_disk "$d"
  done
}
disks_wipe() {
  echo "Wiping bpool disks:"
  for d in "${BPOOL_DISKS[@]}"; do
    wipe_disk "$d"
  done
  echo "Wiping rpool disks:"
  for d in "${RPOOL_DISKS[@]}"; do
    wipe_disk "$d"
  done
  echo "Wiping opool disks:"
  for d in "${OPOOL_DISKS[@]}"; do
    wipe_disk "$d"
  done
}
disks_partition() {
  sync_disks
  echo "Partition bpool disks:"
  for d in "${BPOOL_DISKS[@]}"; do
    if sgdisk -n1:1M:+1G -t1:EF00 "$d" >/dev/null; then
      echo "-> SUCCESS : part1 (EFI  ) partitioned: $d"
    fi
    if sgdisk -n2:0:+1G -t2:BF01 "$d" >/dev/null; then
      echo "-> SUCCESS : part2 (BPOOL) partitioned: $d"
    fi
  done
  echo "Partition rpool disks:"
  for d in "${RPOOL_DISKS[@]}"; do
    if sgdisk -n3:0:0 -t3:BF00 "$d" >/dev/null; then
      echo "-> SUCCESS : part3 (RPOOL) partitioned: $d"
    fi
  done
  echo "Partition opool disks:"
  for d in "${OPOOL_DISKS[@]}"; do
    if sgdisk -n1:0:0 -t1:BF00 "$d" >/dev/null; then
      echo "-> SUCCESS : part1 (OPOOL) partitioned: $d"
    fi
  done
  sync_disks
}
disks_format_efi() {
  echo "Format efi disks:"
  for d in "${BPOOL_DISKS[@]}"; do
    if mkfs.vfat -F32 "${d}-part1" >/dev/null; then
      echo "-> SUCCESS : part1 (RAW  ) formatted to fat32: $d"
    else
      echo "-> ERROR   : part1 (RAW  ) was not formatted: $d"
      exit $CONST_ERR_FORMAT
    fi
  done
}
create_pool() {
  local name="$1"
  local mode="$2"
  local isboot="$3"
  shift 3
  partitions=("$@")
  
  declare -a props=()
  props+=("${PROPS_POOL[@]}")
  props+=("${PROPS_ZFS[@]}")
  [[ $isboot -eq 1 ]] && props+=("${PROPS_GRUB[@]}")

  if zpool create -f "${props[@]}" \
    "$name" "$mode" "${partitions[@]}" ; \
  then
      echo "-> SUCCESS : pool created: $name"
  else
      echo "-> ERROR   : pool NOT created: $name"
  fi
}
create_pools() {
  echo "Adding pools:"
  create_pool "${CFG_ZFS_BPOOL[0]}" "${CFG_ZFS_BPOOL[1]}" 1 "${BPOOL_PARTS[@]}"
  create_pool "${CFG_ZFS_RPOOL[0]}" "${CFG_ZFS_RPOOL[1]}" 0 "${RPOOL_PARTS[@]}"
  create_pool "${CFG_ZFS_OPOOL[0]}" "${CFG_ZFS_OPOOL[1]}" 0 "${OPOOL_PARTS[@]}"
}
create_dataset() {
  local label="$1"
  local mp="$2"
  if zfs create -o canmount=off -o mountpoint="$mp" "$label"; then
      echo "-> SUCCESS : dataset created: $label"
      return 0
  else
      echo "-> ERROR   : dataset NOT created: $label"
      return 1
  fi
}
create_datasets() {
  echo "Adding default datasets:"
  create_dataset "bpool/BOOT" "none"
  create_dataset "rpool/ROOT" "none"
  create_dataset "opool/OPTS" "none"
  echo "Adding custom datasets:"
  for key in "${!DATASET_LB[@]}"; do
    create_dataset "${DATASET_LB[$key]}" "none"
  done
}
destroy_pools
install_essentials
create_property_arrays
create_disk_arrays
create_partition_arrays
create_dataset_arrays
disks_check
disks_wipe
disks_partition
disks_format_efi
create_pools
create_datasets
