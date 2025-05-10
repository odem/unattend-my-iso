#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL APT (CLUSTER)"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1

# Proxy config
if [ "$ISO_TARGET_TYPE" == "live" ] ; then
    if [ ! "$PROXY_IP" = "" ] ; then
        cat << EOF >~/.wgetrc
http_proxy = http://$PROXY_IP
https_proxy = https://$PROXY_IP
EOF
        cat << EOF >/etc/apt/apt.conf.d/95proxy
Acquire::http::Proxy "http://$PROXY_IP";
Acquire::https::Proxy "http://$PROXY_IP";
EOF
    fi
fi

# Sources
cat<< EOF > /etc/apt/sources.list
deb http://deb.debian.org/debian/ bookworm main contrib non-free-firmware
deb http://deb.debian.org/debian/ bookworm-updates main contrib non-free-firmware
#deb http://deb.debian.org/debian/ bookworm-backports main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free-firmware
EOF

# update and install essentials
apt-get update -y && apt-get upgrade -y && apt-get install -y \
    kitty bc git vim make sudo psmisc net-tools tcpdump traceroute \
    ntp lsb-release curl wget gnupg bridge-utils uml-utilities \
    iftop sysstat

# Remove Job From Jobfile
echo "Sucessfully invoked all actions"
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed s#$filename##g -i "$SERVICE"
    echo "Removed job from firstboot script: $(basename "$0")"
fi
echo ""
sleep 1
exit 0
