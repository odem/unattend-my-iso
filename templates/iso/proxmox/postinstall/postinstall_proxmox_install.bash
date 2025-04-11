#!/bin/bash

export DEBIAN_FRONTEND=noninteractive
apt --yes install vim make wget

# Default params (devenv)
PROXMOX_IP=
PROXMOX_HOST=
PROXMOX_DOMAIN=
PROXMOX_DEBURL=http://download.proxmox.com/debian/pve
PROXMOX_KEYURL=https://enterprise.proxmox.com/debian/proxmox-release-bookworm.gpg
script_path="$(dirname "$(realpath "$0")")"
source "$script_path"/hostconfig.env

# Bail if requirements are not met
if  [ "$PROXMOX_IP" = "" ] || [ "$PROXMOX_HOST" = "" ] \
    || [ "$PROXMOX_DOMAIN" = "" ] ; then
    usage
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
    hostname -b "$PROXMOX_HOST"
    echo "$PROXMOX_HOST" | sudo tee /etc/hostname
    cat <<EOF > /etc/hosts

# local
127.0.0.1 localhost
127.0.1.1 $PROXMOX_HOST.local $PROXMOX_HOST

# cluster ips
10.40.1.85 ceph-p1.local ceph-p1
10.40.1.87 ceph-p2.local ceph-p2
10.40.1.89 ceph-p3.local ceph-p3
10.40.1.91 ceph-p4.local ceph-p4
10.40.1.93 proxmox-p1.local proxmox-p1
10.40.1.95 proxmox-p2.local proxmox-p2
10.40.1.97 proxmox-p3.local proxmox-p3
10.40.1.99 proxmox-p4.local proxmox-p4

# ipv6
# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF
}

# Chose Stages by current kernel version
KERNEL=$(uname -r | grep pve)

# Stage 1: Install pve kernel if not present
if [[ "$KERNEL" == "" ]] ; then
    install_kernel
    configure_hostname
    shutdown -r now
fi

# Stage 2: Install pve environment if pve kernel is present
if [[ "$KERNEL" != "" ]] ; then
    install_pve
fi
