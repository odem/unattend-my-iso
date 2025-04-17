#!/bin/bash

# Environment variables
POSTINST_PATH=/opt/umi/postinstall
cd "$POSTINST_PATH" || exit 1
envfile=../config/env.bash
if [[ -f "$envfile" ]]; then
    # shellcheck disable=SC1090
    source "$envfile"
fi

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

# Remove Job From Jobfile
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed s#$filename##g -i "$SERVICE"
fi
exit 0
