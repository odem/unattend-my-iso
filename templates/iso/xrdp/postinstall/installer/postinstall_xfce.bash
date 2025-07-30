#!/bin/bash
# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL DESKTOP (XFCE)"
echo "-------------------------------------------------------------------------"
sleep 3

# Update
apt update && apt upgrade -y

# Desktop environment
apt install -y xfce4 xfce4-goodies
echo "startxfce4" > /etc/skel/.xsession

