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
deb-src http://deb.debian.org/debian/ bookworm main contrib non-free-firmware
deb http://deb.debian.org/debian/ bookworm-updates main contrib non-free-firmware
deb-src http://deb.debian.org/debian/ bookworm-updates main contrib non-free-firmware
#deb http://deb.debian.org/debian/ bookworm-backports main contrib non-free non-free-firmware
#deb-src http://deb.debian.org/debian/ bookworm-backports main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free-firmware
deb-src http://security.debian.org/debian-security bookworm-security main contrib non-free-firmware
EOF

# update and install essentials
apt-get update -y && apt-get upgrade -y 

AUTO_UPDATES="$CFG_AUTO_UPDATES"
if [[ "$AUTO_UPDATES" == "1" ]] ; then
    apt-get install -y unattended-upgrades apt-listchanges
    dpkg-reconfigure -f noninteractive unattended-upgrades
    sed -i '/Unattended-Upgrade::Allowed-Origins/a\        "Debian stable-updates";' \
        /etc/apt/apt.conf.d/50unattended-upgrades
    systemctl enable --now unattended-upgrades.service
    systemctl enable --now apt-daily-upgrade.timer
    cat <<EOF > /etc/apt/apt.conf.d/20auto-upgrades
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF
fi

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
