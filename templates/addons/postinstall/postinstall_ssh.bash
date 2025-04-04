#!/bin/bash

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

