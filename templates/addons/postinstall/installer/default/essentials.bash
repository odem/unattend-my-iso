#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL ESSENTIALS"
echo "-------------------------------------------------------------------------"
sleep 1


apt update -y
apt install -f -y
apt upgrade -y
apt install -y openssh-server attr jq wget curl bc vim sudo 
# apt install -y openssh-server build-essential attr jq vim git sudo make bc \
#     bsdmainutils debconf lsb-release fontconfig psmisc kitty \
#     tcpdump traceroute ntp gnupg curl wget gnupg dnsutils net-tools \
#     bridge-utils uml-utilities iftop sysstat

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
