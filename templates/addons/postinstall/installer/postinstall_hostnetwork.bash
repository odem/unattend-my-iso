#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive

# Environment variables
POSTINST_PATH=/opt/umi/postinstall
cd "$POSTINST_PATH" || exit 1
envfile=../config/env.bash
if [[ -f "$envfile" ]]; then
    # shellcheck disable=SC1090
    source "$envfile"
fi

# Bail if requirements are not met
if  [ "$MANAGE_IP" = "" ] || [ "$MANAGE_HOST" = "" ] \
    || [ "$MANAGE_DOMAIN" = "" ] ; then
    exit 1
fi

# Kernel modules
modprobe bonding
modprobe 8021q
echo "bonding" | tee -a /etc/modules
echo "8021q" | tee -a /etc/modules

# Create Network devices
ip link add "$BRIDGE0_NAME" type bridge
ip link set "$INTERFACE_BOND0_0" master "$BRIDGE0_NAME"
ip link add "$BRIDGE1_NAME" type bridge

# Create network config
cat <<EOF > /etc/network/interfaces
source /etc/network/interfaces.d/sdn

auto $INTERFACE_BOND0_0
iface $INTERFACE_BOND0_0 inet manual
#Ceph und Corosync

auto $INTERFACE_BOND0_1
iface $INTERFACE_BOND0_1 inet manual
#Ceph und Corosync

auto $INTERFACE_BOND1_0
iface $INTERFACE_BOND1_0 inet manual
#Kundennetz und Management

auto $INTERFACE_BOND1_1
iface $INTERFACE_BOND1_1 inet manual
#Kundennetz und Management
EOF

# Fix Bonding for live targets
if [ "$ISO_TARGET_TYPE" == "live" ] ; then
    cat << EOF >>/etc/network/interfaces
auto $BOND0_NAME
iface $BOND0_NAME inet manual
    bond-slaves $INTERFACE_BOND0_0 $INTERFACE_BOND0_1
    bond-mode 802.3ad
    bond-miimon 100
#Ceph und Corosync

auto $BRIDGE0_NAME
iface $BRIDGE0_NAME inet manual
    bridge_ports $BOND0_NAME
    bridge_stp off
    bridge_fd 0
#Ceph und Corosync

auto $BOND1_NAME
iface $BOND1_NAME inet manual
    bond-slaves $INTERFACE_BOND1_0 $INTERFACE_BOND1_1
    bond-mode 802.3ad
    bond-miimon 100
#Ceph und Corosync

auto $BRIDGE1_NAME
iface $BRIDGE1_NAME inet manual
    bridge_ports $BOND1_NAME
    bridge_stp off
    bridge_fd 0
#Ceph und Corosync
EOF

# Simple bridge setup for vm targets (no bonds!)
else
    cat << EOF >>/etc/network/interfaces
auto $BRIDGE0_NAME
iface $BRIDGE0_NAME inet static
    address $MANAGE_IP
    netmask 255.255.255.0
    dns-nameservers $MANAGE_NS1 $MANAGE_NS2
    gateway $MANAGE_GW
    bridge_ports $INTERFACE_BOND0_0
    bridge_stp off
    bridge_fd 0
#Kundennetz und Management

auto $BRIDGE1_NAME
iface $BRIDGE1_NAME inet manual
    bridge_ports $INTERFACE_BOND1_0
    bridge_stp off
    bridge_fd 0
#Kundennetz und Management
EOF
fi

# Attach vlan devices
cat << EOF >>/etc/network/interfaces
auto $INTERFACE_VLAN_HEARTBEAT
iface $INTERFACE_VLAN_HEARTBEAT inet static
    address $HB_IP/24
    vlan-raw-device $BRIDGE1_NAME
#Corosync

auto $INTERFACE_VLAN_STORAGE
iface $INTERFACE_VLAN_STORAGE inet static
    address $STORAGE_IP/24
    vlan-raw-device $BRIDGE1_NAME
#Ceph
EOF

# Hostname
echo "$MANAGE_HOST" > /etc/hostname
hostname -b "$MANAGE_HOST"

# Known hosts
cat <<EOF > /etc/hosts
# local
127.0.0.1 localhost
127.0.1.1 $MANAGE_HOST $MANAGE_HOST.$MANAGE_DOMAIN 

# Management ips
$MANAGE_NET.85 ceph-p1 ceph-p1.local
$MANAGE_NET.87 ceph-p2 ceph-p2.local
$MANAGE_NET.89 ceph-p3 ceph-p3.local
$MANAGE_NET.91 ceph-p4 ceph-p4.local
$MANAGE_NET.93 proxmox-p1 proxmox-p1.local
$MANAGE_NET.95 proxmox-p2 proxmox-p2.local
$MANAGE_NET.97 proxmox-p3 proxmox-p3.local
$MANAGE_NET.99 proxmox-p4 proxmox-p4.local

# Heartbeat ips
$HB_NET.85 ceph-p1 ceph-p1.local
$HB_NET.87 ceph-p2 ceph-p2.local
$HB_NET.89 ceph-p3 ceph-p3.local
$HB_NET.91 ceph-p4 ceph-p4.local
$HB_NET.93 proxmox-p1 proxmox-p1.local
$HB_NET.95 proxmox-p2 proxmox-p2.local
$HB_NET.97 proxmox-p3 proxmox-p3.local
$HB_NET.99 proxmox-p4 proxmox-p4.local

# Storage ips
$STORAGE_NET.85 ceph-p1 ceph-p1.local
$STORAGE_NET.87 ceph-p2 ceph-p2.local
$STORAGE_NET.89 ceph-p3 ceph-p3.local
$STORAGE_NET.91 ceph-p4 ceph-p4.local
$STORAGE_NET.93 proxmox-p1 proxmox-p1.local
$STORAGE_NET.95 proxmox-p2 proxmox-p2.local
$STORAGE_NET.97 proxmox-p3 proxmox-p3.local
$STORAGE_NET.99 proxmox-p4 proxmox-p4.local

# ipv6
# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF

# Restart networking
service networking restart
echo "nameserver $MANAGE_NS1" > /etc/resolv.conf
echo "nameserver $MANAGE_NS2" >> /etc/resolv.conf

# Remove Job From Jobfile
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed s#$filename##g -i "$SERVICE"
fi
exit 0
