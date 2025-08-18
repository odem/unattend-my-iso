#!/bin/bash
# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL Screensaver"
echo "-------------------------------------------------------------------------"
sleep 3

# 
apt -y update && apt upgrade -y
apt install -y dconf-cli

INSTALLER_DIR="$CFG_ANSWERFILE_HOOK_DIR_TARGET"/postinstall/installer

# Global dconf settings
cp -r "$INSTALLER_DIR"/dconf /etc
chmod 755 -R /etc/dconf

# Update dconf
dconf update 
dconf update /

# Screen blanking
xset s off 
xset -dpms
xset s noblank
