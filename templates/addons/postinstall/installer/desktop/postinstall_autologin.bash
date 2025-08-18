#!/bin/bash
# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL Autologin"
echo "-------------------------------------------------------------------------"
sleep 3

# Enable lightdm autologin
sed "/\[Seat:\*\]/a\
autologin-user=$CFG_USER_OTHER_NAME\n\
autologin-user-timeout=0\n" -i /etc/lightdm/lightdm.conf
