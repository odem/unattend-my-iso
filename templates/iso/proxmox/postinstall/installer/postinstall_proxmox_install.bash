#!/bin/bash

# Globals
PROXMOX_DEBURL=http://download.proxmox.com/debian/pve
PROXMOX_KEYURL=https://enterprise.proxmox.com/debian/proxmox-release-bookworm.gpg

# Environment variables
POSTINST_PATH=/opt/umi/postinstall
cd "$POSTINST_PATH" || exit 1
envfile=../config/env.bash
if [[ -f "$envfile" ]]; then
    # shellcheck disable=SC1090
    source "$envfile"
fi

install_kernel() {
    sudo -E apt --yes update && sudo -E apt --yes install wget python3.11-venv
    echo "deb [arch=amd64] $PROXMOX_DEBURL bookworm pve-no-subscription" |
        sudo tee /etc/apt/sources.list.d/pve-install-repo.list
    sudo wget "$PROXMOX_KEYURL" \
        -O /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg
    sudo -E apt --yes update && sudo -E apt --yes full-upgrade
    sudo -E apt --yes install pve-kernel-6.2
    [[ -f /etc/apt/sources.list.d/pve-enterprise.list ]] && \
        rm -rf /etc/apt/sources.list.d/pve-enterprise.list
}

install_pve() {
    sudo -E apt --yes install proxmox-ve open-iscsi
    sudo -E apt --yes remove linux-image-amd64 'linux-image-6.1*'
    sudo -E apt --yes remove os-prober
    sudo -E apt --yes install dnsmasq build-essential python3.11-dev
    sudo -E update-grub

    # Apt Sources (Proxmox)
    echo "deb [arch=amd64] http://download.proxmox.com/debian/pve bookworm pve-no-subscription" > /etc/apt/sources.list.d/pve-install-repo.list
    wget https://enterprise.proxmox.com/debian/proxmox-release-bookworm.gpg -O /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg
    sha512sum /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg
    rm -rf /etc/apt/sources.list.d/pve-enterprise.list

    # Update
    apt update
    apt --yes -f upgrade
}

configure_hostname() {
    hostname -b "$MANAGE_HOST"
    echo "$MANAGE_HOST" | sudo tee /etc/hostname
}

# Chose Stages by current kernel version
KERNEL=$(uname -r | grep pve)

# Stage 1: Install pve kernel if not present
if [[ "$KERNEL" == "" ]] ; then
    install_kernel
    configure_hostname
    #configure_hosts
    shutdown -r now
fi

# Stage 2: Install pve environment if pve kernel is present
if [[ "$KERNEL" != "" ]] ; then
    install_pve
    # Remove Job From Jobfile
    SERVICE=/firstboot.bash
    if [[ -f "$SERVICE" ]]; then
        filename="$(basename "$0")"
        # shellcheck disable=SC2086
        sed s#$filename##g -i "$SERVICE"
    fi
fi
exit 0
