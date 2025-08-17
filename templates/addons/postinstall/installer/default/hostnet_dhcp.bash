#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

DEFAULT_NIC_0=""
DEFAULT_NIC_1=""

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL HOSTNET_DHCP"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1

if [[ "$DEFAULT_NIC_0" != "" ]] ; then
    # Create network config
    cat <<EOF > /etc/network/interfaces
auto $DEFAULT_NIC_0
iface $DEFAULT_NIC_0 inet dhcp
# Default uplink nic 0
EOF
fi

if [[ "$DEFAULT_NIC_1" != "" ]] ; then
    # Create network config
    cat <<EOF >> /etc/network/interfaces

auto $DEFAULT_NIC_1
iface $DEFAULT_NIC_1 inet dhcp
# Uplink nic 1
EOF
fi

systemctl daemon-reload
systemctl restart networking

# Remove Job From Jobfile
echo "Sucessfully invoked all actions"
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed -i "/$filename/d" "$SERVICE"
    echo "Removed job from firstboot script: $(basename "$0")"
fi
echo ""
sleep 1
exit 0
