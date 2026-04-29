#!/bin/bash
# shellcheck disable=SC1090,1091

# -- Defaults
MNTDIR="/target"
CODENAME="trixie"
declare -A DATASET_LB
declare -A DATASET_MP

# -- Globals ---
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# -- Error Constants
CONST_ERR_MNTDIR=100
CONST_ERR_EFIDIR=101
CONST_ERR_EFIMOUNT=102
CONST_ERR_ZFSSETMP=103
CONST_ERR_ZFSMOUNT=104
CONST_ERR_ZFSUNMOUNT=105

[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

create_dataset_arrays() {
  # echo "INPUT DATASETS: ${CFG_ZFS_DATASETS[*]}"
  for entry in "${CFG_ZFS_DATASETS[@]}"; do
    entry=${entry//\'/}
    IFS=',' read -r name mountpoint label <<<"$entry"
    name=${name// /}
    mountpoint=${mountpoint// /}
    label=${label// /}
    DATASET_LB["$name"]=$label
    DATASET_MP["$name"]=$mountpoint
  done
  # echo "DATASET_LB: ${DATASET_LB[*]}"
  # echo "DATASET_MP: ${DATASET_MP[*]}"
}

install_debootstrap_debian() {
  echo "Installing debian $CODENAME via debootstrap:"
  if [[ ! -e "$MNTDIR" ]]; then
    mkdir -p "$MNTDIR"
  fi
  if [[ -e "$MNTDIR" ]]; then
    if debootstrap "$CODENAME" "$MNTDIR"; then
      echo "-> SUCCESS : debootstrapped $CODENAME into $MNTDIR"
    else
      echo "-> ERROR   : debootstrap $CODENAME failed in $MNTDIR"
    fi
  else
    echo "-> ERROR   : $MNTDIR does not exist"
    exit $CONST_ERR_MNTDIR
  fi
}

mount_debootstrap_folders_default() {
  echo "Mounting default chroot folders:"
  mkdir -p "$MNTDIR"/dev "$MNTDIR"/proc "$MNTDIR"/sys "$MNTDIR"/run
  mount --bind /dev "$MNTDIR"/dev
  mount --bind /dev/pts "$MNTDIR"/dev/pts
  mount --bind /proc "$MNTDIR"/proc
  mount --rbind /sys "$MNTDIR"/sys
  mount --make-rslave "$MNTDIR"/sys
  mount --bind /run "$MNTDIR"/run
  echo "-> SUCCESS : chroot folders mounted into $MNTDIR"
}

mount_debootstrap_folder_zfs() {
  local ismounted=""
  local mp="$1"
  local label="$2"
  ismounted=0
  if mount | grep -q "$label"; then
    ismounted=1
  fi
  if [[ $ismounted -eq 0 ]]; then
    if zfs set canmount=noauto mountpoint="$mp" "$label"; then
      if zfs mount "$label"; then
        echo "-> SUCCESS : zfs root dataset mounted into $mp"
      else
        echo "-> ERROR   : zfs root dataset NOT mounted into $mp"
        return "$CONST_ERR_ZFSMOUNT"
      fi
    else
      echo "-> ERROR   : zfs properties NOT set to $mp"
      return "$CONST_ERR_ZFSSETMP"
    fi
  else
    echo "-> SUCCESS : zfs root dataset already mounted on $mp"
  fi
}
unmount_debootstrap_folder_zfs() {
  local ismounted=""
  local mp="$1"
  local label="$2"
  ismounted=0
  if mount | grep -q "$label"; then
    ismounted=1
  fi
  if [[ $ismounted -eq 1 ]]; then
    if zfs set canmount=off mountpoint=none "$label"; then
      echo "-> SUCCESS : zfs unset mountpoint on $mp"
      if zfs unmount "$label"; then
        echo "-> SUCCESS : zfs dataset unmounted from $mp"
      else
        echo "-> ERROR   : zfs root dataset NOT unmounted from $mp"
        return "$CONST_ERR_ZFSMOUNT"
      fi
    else
      echo "-> ERROR   : zfs properties NOT set to $mp"
      return "$CONST_ERR_ZFSSETMP"
    fi
  else
    echo "-> SUCCESS : zfs root dataset not mounted on $mp"
  fi
}
mount_debootstrap_folders_zfs_root() {
  echo "Mounting zfs chroot folders (root):"
  for key in "${!DATASET_LB[@]}"; do
    local mp="${MNTDIR}${DATASET_MP[$key]}"
    local label="${DATASET_LB[$key]}"
    if [[ "$mp" == "$MNTDIR/" ]]; then
      mount_debootstrap_folder_zfs "$mp" "$label"
    fi
  done
}
mount_debootstrap_folders_zfs_custom() {
  echo "Mounting zfs chroot folders (custom):"
  for key in "${!DATASET_LB[@]}"; do
    local mp="${MNTDIR}${DATASET_MP[$key]}"
    local label="${DATASET_LB[$key]}"
    if [[ "$mp" != "$MNTDIR/" ]]; then
      mount_debootstrap_folder_zfs "$mp" "$label"
    fi
  done
}
unmount_debootstrap_folders_zfs_root() {
  echo "unmounting zfs chroot folders (root):"
  for key in "${!DATASET_LB[@]}"; do
    local mp="${MNTDIR}${DATASET_MP[$key]}"
    local label="${DATASET_LB[$key]}"
    if [[ "$mp" == "$MNTDIR/" ]]; then
      unmount_debootstrap_folder_zfs "$mp" "$label"
    fi
  done
}
unmount_debootstrap_folders_zfs_custom() {
  echo "Unmounting zfs chroot folders (custom):"
  for key in "${!DATASET_LB[@]}"; do
    local mp="${MNTDIR}${DATASET_MP[$key]}"
    local label="${DATASET_LB[$key]}"
    if [[ "$mp" != "$MNTDIR/" ]]; then
      unmount_debootstrap_folder_zfs "$mp" "$label"
    fi
  done
}
mount_efi_folders() {
  echo "Mounting efi partition:"
  read -r -a BPOOL_DISKS <<<"${CFG_ZFS_BPOOL[2]}"
  local efidev="${BPOOL_DISKS[0]}-part1"
  mkdir -p "$MNTDIR"/sys/firmware/efi
  mount --bind /sys/firmware/efi/efivars "$MNTDIR"/sys/firmware/efi/efivars
  # mount --make-rslave "$MNTDIR"/sys/firmware/efi/efivars
  mkdir -p "$MNTDIR"/boot/efi
  if [[ -e "$MNTDIR"/boot/efi ]]; then
    if mount "$efidev" "$MNTDIR"/boot/efi; then
      echo "-> SUCCESS : efi partition mounted into $MNTDIR/boot/efi"
    else
      echo "-> ERROR   : efi partition NOT mounted into $MNTDIR/boot/efi"
      exit $CONST_ERR_EFIMOUNT
    fi
  else
    echo "-> ERROR   : $MNTDIR/boot/efi does not exist!"
    exit $CONST_ERR_EFIDIR
  fi
}
install_debootstrap_apt() {
  cat <<EOF >"$MNTDIR"/usr/local/bin/setup-chroot-apt.bash
#!/bin/bash
set -e

# echo "Hostname..."
# echo "$HOSTNAME" > /etc/hostname

cat > /etc/apt/sources.list <<EOL
deb http://deb.debian.org/debian trixie main contrib non-free-firmware
deb http://deb.debian.org/debian trixie-updates main contrib non-free-firmware
deb http://security.debian.org/debian-security trixie-security main contrib non-free-firmware
EOL
apt update
apt install --yes qemu-guest-agent bochs console-setup locales initramfs-tools \
  firmware-linux-free \
  console-setup \
  kbd \
  openssh-server
apt install -y linux-headers-"$(uname -r)" linux-image-amd64 \
zfs-initramfs initramfs-tools zfs-dkms grub-efi-amd64 shim-signed \
  dpkg-dev linux-headers-generic linux-image-generic 
mkdir -p /etc/dkms
echo REMAKE_INITRD=yes > /etc/dkms/zfs.conf
modprobe zfs
EOF
  chmod +x "$MNTDIR"/usr/local/bin/setup-chroot-apt.bash
  chroot "$MNTDIR" /bin/bash /usr/local/bin/setup-chroot-apt.bash
}
install_debootstrap_grub() {
  cat <<EOF >"$MNTDIR"/usr/local/bin/setup-chroot-grub.bash
#!/bin/bash
set -e
apt purge --yes os-prober
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=debian
grub-probe /boot
update-initramfs -c -k all
update-grub
EOF
  chmod +x "$MNTDIR"/usr/local/bin/setup-chroot-grub.bash
  chroot "$MNTDIR" /bin/bash /usr/local/bin/setup-chroot-grub.bash
}
install_debootstrap_finalize() {
  cat <<EOF >"$MNTDIR"/usr/local/bin/setup-chroot-finalize.bash
#!/bin/bash
set -e
USERNAME=deploy
useradd -m -G sudo -s /bin/bash \$USERNAME
echo "\$USERNAME:\${USERNAME}pass" | chpasswd
echo "root:rootpass" | chpasswd
# zfs
systemctl enable zfs.target
EOF
  chmod +x "$MNTDIR"/usr/local/bin/setup-chroot-finalize.bash
  chroot "$MNTDIR" /bin/bash /usr/local/bin/setup-chroot-finalize.bash
}
unmount_chroot() {
  sync
  umount -R "$MNTDIR"/run
  umount -R "$MNTDIR"/proc
  umount -R "$MNTDIR"/sys
  umount -R "$MNTDIR"/dev/pts
  umount -R "$MNTDIR"/dev
  umount "$MNTDIR"/boot/efi
}
finalize_zfs_mountpoints() {
  echo "Finalize zfs mountpoints:"
  for key in "${!DATASET_LB[@]}"; do
    local mp="${DATASET_MP[$key]}"
    local label="${DATASET_LB[$key]}"
    if zfs set canmount=noauto mountpoint="$mp" "$label"; then
      echo "-> SUCCESS : Mountpoint on $label updated to '$mp'"
    else
      echo "-> ERROR   : Mountpoint on $label NOT updated to '$mp'"
      exit $CONST_ERR_ZFSUNMOUNT
    fi
  done
  zfs unmount -a
  zpool export -a
}
create_dataset_arrays
mount_debootstrap_folders_zfs_root
install_debootstrap_debian
mount_debootstrap_folders_default
mount_debootstrap_folders_zfs_custom
mount_efi_folders
install_debootstrap_apt
install_debootstrap_grub
install_debootstrap_finalize
unmount_chroot
unmount_debootstrap_folders_zfs_custom
unmount_debootstrap_folders_zfs_root
finalize_zfs_mountpoints
