#!/bin/bash
# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL Powerbuttons"
echo "-------------------------------------------------------------------------"
sleep 3

# Global policy to disable power actions via pkla file 
# (Legacy: Working up to Debian12)
INSTALLER_DIR="$CFG_ANSWERFILE_HOOK_DIR_TARGET"/postinstall/installer
POLKIT_DIR_PKLA="/etc/polkit-1/localauthority/50-local.d/"
mkdir -p "$POLKIT_DIR_PKLA" 
cp -r  "$INSTALLER_DIR"/polkit/* "$POLKIT_DIR_PKLA"/
chmod 755 -R "$POLKIT_DIR_PKLA"

# Global policy to disable power actions via js rules 
# (State-of-the-art: Needed since Debian13)
POLKIT_DIR="/etc/polkit-1/rules.d"
mkdir -p "$POLKIT_DIR" 
cp -r  "$INSTALLER_DIR"/polkit_js/* "$POLKIT_DIR"/
chmod 755 -R "$POLKIT_DIR"
