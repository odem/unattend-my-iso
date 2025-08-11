#!/bin/bash


# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,SC1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL APT"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1

# shellcheck disable=SC1091
source /etc/os-release
CODENAME=$VERSION_CODENAME

# Sources
cat<< EOF > /etc/apt/sources.list
deb http://deb.debian.org/debian/ $CODENAME main contrib non-free-firmware
deb-src http://deb.debian.org/debian/ $CODENAME main contrib non-free-firmware
deb http://deb.debian.org/debian/ $CODENAME-updates main contrib non-free-firmware
deb-src http://deb.debian.org/debian/ $CODENAME-updates main contrib non-free-firmware
#deb http://deb.debian.org/debian/ $CODENAME-backports main contrib non-free non-free-firmware
#deb-src http://deb.debian.org/debian/ $CODENAME-backports main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security $CODENAME-security main contrib non-free-firmware
deb-src http://security.debian.org/debian-security $CODENAME-security main contrib non-free-firmware
EOF

# update and install essentials
apt-get update -y
apt-get install -f -y
apt-get upgrade -y
apt-get install -y apt-utils
apt-get autoremove

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
