#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL HOSTNET_STATIC"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1

# Bail if requirements are not met
if  [ "$DEFAULT_IP" = "" ] || [ "$DEFAULT_HOST" = "" ] \
    || [ "$DEFAULT_DOMAIN" = "" ] ; then
    exit 1
fi

# Create network config
cat <<EOF > /etc/network/interfaces

auto $DEFAULT_NIC_0
iface $DEFAULT_NIC_0 inet static
    address $DEFAULT_IP
    netmask $DEFAULT_NETMASK
    dns-nameservers $DEFAULT_NS1 $DEFAULT_NS2
    gateway $DEFAULT_GW
#Default Uplink

EOF

# Restart networking
service networking restart
echo "nameserver $DEFAULT_NS1" > /etc/resolv.conf
echo "nameserver $DEFAULT_NS2" >> /etc/resolv.conf

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
