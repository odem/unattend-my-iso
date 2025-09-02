#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL ESSENTIALS"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1

# Update and install
apt update -y
apt install -f -y
apt upgrade -y
apt install -y openssh-server rsyslog attr jq wget curl bc git vim make xxd \
    sudo qemu-guest-agent eza bat chrony lsb-release gnupg iptables zip unzip
apt install -y \
    kitty psmisc\
    net-tools tcpdump traceroute bridge-utils uml-utilities \
    iftop sysstat
echo ""
apt remove -y exim4-base
apt autoremove

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
