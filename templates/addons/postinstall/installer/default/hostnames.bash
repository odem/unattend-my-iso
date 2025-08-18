#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL HOSTNAMES"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1

# Adjust test name
if [[ "$DEFAULT_DEPLOYMENT_MODE" != "live" ]] ; then
    DEFAULT_HOST="tst-$DEFAULT_HOST"
fi

# Hostname
echo "$DEFAULT_HOST" > /etc/hostname
hostname -b "$DEFAULT_HOST"

# Common hosts
cat <<EOF > /etc/hosts
# local
127.0.0.1 localhost
127.0.1.1 $DEFAULT_HOST $DEFAULT_HOST.$DEFAULT_DOMAIN 

# ipv6
# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF

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
