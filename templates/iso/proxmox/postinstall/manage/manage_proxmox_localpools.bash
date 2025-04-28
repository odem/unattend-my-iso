#!/bin/bash

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Vars
POOLDIR=/srv/data/pools
POOL_LOCAL=local-lvm
POOL_DEFAULT=local

# Prepare
mkdir -p "$POOLDIR/$POOL_LOCAL"
chown root:root -R "$POOLDIR"
chmod 755 -R "$POOLDIR"

# Create default pool via directory link
pvesm remove "$POOL_DEFAULT"
pvesm add dir "$POOL_LOCAL" --path "$POOLDIR/$POOL_LOCAL" \
    --content images,iso,vztmpl,backup
pvesm status
systemctl restart pvedaemon




