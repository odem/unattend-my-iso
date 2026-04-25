#!/usr/bin/env bash
set -euo pipefail

MNTDIR="/mnt"
echo "[0/11] Set variables..."
DISKS=(
  "/dev/disk/by-id/virtio-DISK-0"
  "/dev/disk/by-id/virtio-DISK-1"
  "/dev/disk/by-id/virtio-DISK-2"
  "/dev/disk/by-id/virtio-DISK-3"
)

HOSTNAME="debian-zfs"
USERNAME="user"

POOLNAME_RPOOL="rpool"
POOLNAME_BPOOL="bpool"

echo "[1/11] Building device arrays..."
EFI_DEVS=()
BPOOL_DEVS=()
RPOOL_DEVS=()
for d in "${DISKS[@]}"; do
  EFI_DEVS+=("${d}-part1")
  BPOOL_DEVS+=("${d}-part2")
  RPOOL_DEVS+=("${d}-part3")
done

echo "[2/11] Installing prerequisites..."
apt update
apt install -y debootstrap parted gdisk dosfstools \
  zfsutils-linux zfs-dkms linux-headers-"$(uname -r)"
dkms autoinstall
modprobe zfs
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
echo "[3/11] Checking, wiping and partitioning disks..."
for d in "${DISKS[@]}"; do
  if [[ ! -e "$d" ]]; then
    echo "ERROR: Disk not found: $d"
    echo "Check /dev/disk/by-id/ in your VM."
    exit 1
  fi
done

echo ""
for d in "${DISKS[@]}"; do
  echo ""
  echo "  -> Wiping $d"
  sgdisk --zap-all "$d"
  wipefs -a "$d" || true

  echo ""
  echo "  -> Creating partitions on $d"
  sgdisk -n1:1M:+512M -t1:EF00 "$d"   # EFI
  sgdisk -n2:0:+1G    -t2:BF01 "$d"   # bpool
  sgdisk -n3:0:0      -t3:BF00 "$d"   # rpool
  echo ""
done

echo "Syncing disks and fs"
partprobe
udevadm trigger
udevadm settle
sync

echo "[4/11] Formatting EFI partition (first disk only)..."
mkfs.vfat -F32 "${EFI_DEVS[0]}"

echo "[5/11] Creating ZFS pools (mirror across 4 disks)..."
udevadm trigger
udevadm settle
zpool create -f \
  -o ashift=12 \
  -o autotrim=on \
  -o compatibility=grub2 \
  -O acltype=posixacl \
  -O xattr=sa \
  -O relatime=on \
  -O normalization=formD \
  -O mountpoint=none \
  "$POOLNAME_BPOOL" mirror "${BPOOL_DEVS[@]}"
# -o cachefile=/etc/zfs/zpool.cache \
  # -O compression=lz4 \

zpool create -f \
  -o ashift=12 \
  -o autotrim=on \
  -O acltype=posixacl \
  -O xattr=sa \
  -O relatime=on \
  -O normalization=formD \
  -O mountpoint=none \
  "$POOLNAME_RPOOL" mirror "${RPOOL_DEVS[@]}"
# -o cachefile=/etc/zfs/zpool.cache \
  # -O compression=lz4 \

echo "[6/11] Creating datasets..."
[[ -d "$MNTDIR" ]] || mkdir "$MNTDIR"
zfs create -o canmount=off -o mountpoint=none bpool/BOOT
zfs create -o canmount=noauto -o mountpoint=none bpool/BOOT/debian
zfs create -o canmount=off -o mountpoint=none rpool/ROOT
zfs create -o canmount=noauto -o mountpoint=none rpool/ROOT/debian
# zfs create -o mountpoint=none rpool/home
# zfs create -V 4G -b $(getconf PAGESIZE) -o compression=zle \
#     -o logbias=throughput -o sync=always \
#     -o primarycache=metadata -o secondarycache=none \
#     -o com.sun:auto-snapshot=false rpool/swap
# mkswap -f /dev/zvol/rpool/swap
# echo /dev/zvol/rpool/swap none swap discard 0 0 >> /etc/fstab
# echo RESUME=none > /etc/initramfs-tools/conf.d/resume

# chroot mounts
echo "Create Chroot mounts"
# sudo mount -t zfs rpool/ROOT/debian "$MNTDIR"
# [[ -d "$MNTDIR"/boot ]] || mkdir "$MNTDIR"/boot
# sudo mount -t zfs bpool/BOOT/debian "$MNTDIR"/boot

zfs set mountpoint="$MNTDIR" rpool/ROOT/debian
zfs set mountpoint="$MNTDIR"/boot bpool/BOOT/debian
zfs mount rpool/ROOT/debian
zfs mount bpool/BOOT/debian

echo "[7/11] Copying ZFS cache..."
# mkdir -p "$MNTDIR"/etc/zfs
# cp /etc/zfs/zpool.cache "$MNTDIR"/etc/zfs/

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
echo "[9/11] Installing base system..."
debootstrap trixie "$MNTDIR"
# mount --rbind /proc "$MNTDIR"/proc
# mount --make-rslave "$MNTDIR"/proc

echo "[8/11] Preparing chroot..."
mkdir -p "$MNTDIR"/dev "$MNTDIR"/proc "$MNTDIR"/sys "$MNTDIR"/run
mount --rbind /dev  "$MNTDIR"/dev
mount --make-rslave "$MNTDIR"/dev
# mount --rbind /dev/pts  "$MNTDIR"/dev/pts
# mount --make-rslave "$MNTDIR"/dev/pts
# mount -t devpts devpts "$MNTDIR"/dev/pts -o gid=5,mode=620
mount --rbind /proc "$MNTDIR"/proc
mount --make-rslave "$MNTDIR"/proc
mount --rbind /sys  "$MNTDIR"/sys
mount --make-rslave "$MNTDIR"/sys
mount --rbind /run  "$MNTDIR"/run
mount --make-rslave "$MNTDIR"/run

echo "Preparing chroot (efi)..."
mkdir -p "$MNTDIR"/sys/firmware/efi 
mount --rbind /sys/firmware/efi/efivars "$MNTDIR"/sys/firmware/efi/efivars
mount --make-rslave "$MNTDIR"/sys/firmware/efi/efivars
mkdir -p "$MNTDIR"/boot/efi
mount "${EFI_DEVS[0]}" "$MNTDIR"/boot/efi


cat <<EOF > "$MNTDIR"/root/setup-chroot.sh
#!/bin/bash
set -e

echo "Hostname..."
echo "$HOSTNAME" > /etc/hostname

echo "APT sources..."
cat > /etc/apt/sources.list <<EOL
deb http://deb.debian.org/debian trixie main contrib non-free-firmware
deb http://deb.debian.org/debian trixie-updates main contrib non-free-firmware
deb http://security.debian.org/debian-security trixie-security main contrib non-free-firmware
EOL

# Test mounts

echo "Installing kernel, ZFS, GRUB..."
apt update
apt install --yes qemu-guest-agent bochs console-setup locales initramfs-tools \
  firmware-linux-free \
  console-setup \
  kbd \
  openssh-server
apt install -y linux-headers-"$(uname -r)" linux-image-amd64 \
zfs-initramfs initramfs-tools zfs-dkms grub-efi-amd64 shim-signed \
  dpkg-dev linux-headers-generic linux-image-generic \
echo REMAKE_INITRD=yes > /etc/dkms/zfs.conf
modprobe zfs

#echo "Fixing ZFS mountpoints..."
# zpool set cachefile=/etc/zfs/zpool.cache rpool
# zfs set canmount=noauto rpool/ROOT/debian
# zfs mount -a

echo "Installing GRUB..."
apt purge --yes os-prober
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=debian
grub-probe /boot
update-initramfs -c -k all
update-grub

# mkdir /etc/zfs/zfs-list.cache
# touch /etc/zfs/zfs-list.cache/bpool
# touch /etc/zfs/zfs-list.cache/rpool
# zed -F &

echo "Creating user..."
USERNAME=user
useradd -m -G sudo -s /bin/bash \$USERNAME
echo "\$USERNAME:\${USERNAME}pass" | chpasswd
echo "root:rootpass" | chpasswd

echo "Enabling ZFS services..."
# systemctl enable zfs-import-cache
# systemctl enable zfs-mount
systemctl enable zfs.target

echo "Done."
EOF

chmod +x "$MNTDIR"/root/setup-chroot.sh
chroot "$MNTDIR" /bin/bash /root/setup-chroot.sh

# User
cp /home/user/.ssh/authorized_keys /mnt/user/.ssh/authorized_keys

echo "[10/11] Cleanup..."
sync
# umount -R "$MNTDIR"/run/live
umount -R "$MNTDIR"/run
umount -R "$MNTDIR"/proc
umount -R "$MNTDIR"/sys
umount -R "$MNTDIR"/dev
umount "$MNTDIR"/boot/efi
zfs umount "$MNTDIR"/boot
zfs umount "$MNTDIR"

zfs unmount -a
zfs set mountpoint=/ rpool/ROOT/debian
zfs set mountpoint=/boot bpool/BOOT/debian
# zpool export -a

echo "[11/11] DONE. Reboot system."

