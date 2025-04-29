#!/bin/bash

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL HOSTNET_DHCP"
echo "-------------------------------------------------------------------------"
sleep 1

# Bail if requirements are not met
if  [ "$DEFAULT_IP" = "" ] || [ "$DEFAULT_HOST" = "" ] \
    || [ "$DEFAULT_DOMAIN" = "" ] ; then
    exit 1
fi

# Create network config
cat <<EOF > /etc/network/interfaces

auto $DEFAULT_NIC_0
iface $DEFAULT_NIC_0 inet dhcp
#Default Uplink

EOF

# Remove Job From Jobfile
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed s#$filename##g -i "$SERVICE"
fi
exit 0
