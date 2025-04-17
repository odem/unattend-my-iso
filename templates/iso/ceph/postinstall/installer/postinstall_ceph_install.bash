#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

# Sources
echo "deb https://download.ceph.com/debian-squid/ bookworm main" \
    | sudo tee /etc/apt/sources.list.d/ceph.list
curl -fsSL https://download.ceph.com/keys/release.asc \
    | sudo tee /etc/apt/trusted.gpg.d/ceph.asc

# Installation
sudo apt update && sudo apt upgrade -y
sudo apt install -y cephadm ceph ceph-common ceph-fuse attr bsdmainutils
sudo cephadm version
sudo ceph -v

# Podman overlay dir
mkdir -p /srv/data/podman
PODMAN_OVERLAY_DIR="/srv/data/podman/containers/storage"
cat <<EOF > /etc/containers/storage.conf
[storage]
  driver = "overlay"
  runroot = "/run/user/1000"
  graphroot = "$PODMAN_OVERLAY_DIR"
  [storage.options]
    size = ""
    remap-uids = ""
    remap-gids = ""
    ignore_chown_errors = ""
    remap-user = ""
    remap-group = ""
    mount_program = "/usr/bin/fuse-overlayfs"
    mountopt = ""
    [storage.options.thinpool]
      autoextend_percent = ""
      autoextend_threshold = ""
      basesize = ""
      blocksize = ""
      directlvm_device = ""
      directlvm_device_force = ""
      fs = ""
      log_level = ""
      min_free_space = ""
      mkfsarg = ""
      mountopt = ""
      use_deferred_deletion = ""
      use_deferred_removal = ""
      xfs_nospace_max_retries = ""
EOF

# Remove Job From Jobfile
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed s#$filename##g -i "$SERVICE"
fi
exit 0
