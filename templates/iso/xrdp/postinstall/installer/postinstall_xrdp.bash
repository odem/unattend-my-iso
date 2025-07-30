#!/bin/bash
# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive
USERNAME="$CFG_USER_OTHER_NAME"
RDP_DIR="$(dirname "$0")"/xrdp

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL XRDP"
echo "-------------------------------------------------------------------------"
sleep 3

# Update
apt update && apt upgrade -y

# xrdp
apt install -y xrdp
cp -r "$RDP_DIR"/* /etc/xrdp/
systemctl enable xrdp

# Configure user
adduser "$USERNAME" ssl-cert
cp /etc/skel/.xsession /home/"$USERNAME"/.xsession
chown "$USERNAME":"$USERNAME" /home/"$USERNAME"/.xsession

# Restart services
systemctl restart xrdp
systemctl restart xrdp-sesman

