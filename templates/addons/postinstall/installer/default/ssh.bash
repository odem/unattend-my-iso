#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL SSH"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1

if [[ -f /opt/umi/ssh/id_rsa.pub ]] ; then
    mkdir -p /root/.ssh
    cp /opt/umi/ssh/id_rsa* /root/.ssh/
    chmod 0600 /root/.ssh/id_rsa*
fi
if [[ -f /opt/umi/ssh/authorized_keys ]] ; then
    cp /opt/umi/ssh/authorized_keys /root/.ssh/authorized_keys
fi
if [[ -f /opt/umi/ssh/sshd_config ]] ; then
    cp /opt/umi/ssh/sshd_config /etc/ssh/sshd_config
fi
systemctl enable ssh
systemctl restart ssh
echo ""

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
