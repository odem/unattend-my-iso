#!/bin/bash

# Default params (devenv)
PROXY_IP=
BRIDGE0_NAME="vmbr0"
BRIDGE1_NAME="vmbr1"
BOND1_NAME=bond1
INTERFACE_BACK="enp0s4"
INTERFACE_BOND0="enp0s5"
INTERFACE_BOND1="enp0s6"
INTERFACE_CEPH="enp0s7"
PROXMOX_IP=
TIME_IP=
PROXMOX_HOST=
PROXMOX_DOMAIN=
PROXMOX_GW=
PROXMOX_NS1=
PROXMOX_NS2=
export DEBIAN_FRONTEND=noninteractive

# Read custom config
script_path="$(dirname "$(realpath "$0")")"
source "$script_path"/hostconfig.env

# Bail if requirements are not met
if  [ "$PROXMOX_IP" = "" ] || [ "$PROXMOX_HOST" = "" ] \
    || [ "$PROXMOX_DOMAIN" = "" ] ; then
    usage
fi

# Bonding drivers
cd /opt/postinstall/debs/archives || exit 1
dpkg -i ./*.deb
modprobe bonding
echo "bonding" | tee -a /etc/modules
echo "8021q" | tee -a /etc/modules

# Configure network devices
# WARNING: Empty lines between paragraphs do matter!
ip link add "$BRIDGE0_NAME" type bridge
ip link set "$INTERFACE_BACK" master "$BRIDGE0_NAME"
ip link add link "$BRIDGE0_NAME" name "$INTERFACE_VLAN_STORAGE" type vlan id "$VLAN_STORAGE"
ip link set "$INTERFACE_VLAN_STORAGE" up
ip link add link "$BRIDGE0_NAME" name "$INTERFACE_VLAN_HEARTBEAT" type vlan id "$VLAN_HEARTBEAT"
ip link set "$INTERFACE_VLAN_HEARTBEAT" up
cat <<EOF > /etc/network/interfaces
source /etc/network/interfaces.d/sdn

auto $INTERFACE_BACK
iface $INTERFACE_BACK inet manual
#Ceph und Corosync

auto $INTERFACE_BOND0
iface $INTERFACE_BOND0 inet manual
#Ceph und Corosync


auto $INTERFACE_BOND1
iface $INTERFACE_BOND1 inet manual
#Kundennetz und Management


auto $INTERFACE_CEPH
iface $INTERFACE_CEPH inet manual
#Kundennetz und Management

auto $BRIDGE0_NAME
iface $BRIDGE0_NAME inet static
    address $PROXMOX_IP
    netmask 255.255.255.0
    dns-nameservers $PROXMOX_NS1 $PROXMOX_NS2
    gateway $PROXMOX_GW
    bridge_ports $INTERFACE_BACK
    bridge_stp off
    bridge_fd 0
#Kundennetz und Management
EOF

# Fix Bonding for live targets
if [ "$ISO_TARGET_TYPE" == "live" ] ; then
    cat << EOF >>/etc/network/interfaces
auto $BOND1_NAME
iface $BOND1_NAME inet manual
    bond-slaves $INTERFACE_BOND0 $INTERFACE_BOND1
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
else
    cat << EOF >>/etc/network/interfaces
auto $BRIDGE1_NAME
iface $BRIDGE1_NAME inet manual
    bridge_ports $INTERFACE_BOND0
    bridge_stp off
    bridge_fd 0
#Kundennetz und Management
EOF
fi
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

# Proxy config
if [ ! "$PROXY_IP" = "" ] ; then
    cat << EOF >~/.wgetrc
http_proxy = http://$PROXY_IP
https_proxy = https://$PROXY_IP
EOF
    cat << EOF >/etc/apt/apt.conf.d/95proxy
Acquire::http::Proxy "http://$PROXY_IP";
Acquire::https::Proxy "http://$PROXY_IP";
EOF
#     mkdir -p /etc/pve
#     touch /etc/pve/datacenter.cfg
#     cat << EOF >/etc/pve/datacenter.cfg
# http_proxy: http://$PROXY_IP
# EOF
fi

# Sources
cat<< EOF > /etc/apt/sources.list
deb http://deb.debian.org/debian/ bookworm main contrib non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free-firmware
deb http://deb.debian.org/debian/ bookworm-updates main contrib non-free-firmware
EOF

# Restart networking
service networking restart
echo "nameserver $PROXMOX_NS1" > /etc/resolv.conf
echo "nameserver $PROXMOX_NS2" >> /etc/resolv.conf

# Initial update and tool installation
apt-get -y update
apt-get -y upgrade
apt-get -y install git vim make sudo psmisc net-tools tcpdump traceroute \
    keyboard-configuration console-setup bc

export DEBIAN_FRONTEND=noninteractive
debconf-set-selections <<EOF
keyboard-configuration  keyboard-configuration/modelcode    select pc105
keyboard-configuration  keyboard-configuration/layoutcode   select de
keyboard-configuration  keyboard-configuration/variantcode  select nodeadkeys
keyboard-configuration  keyboard-configuration/xkb-keymap   select de
EOF
dpkg-reconfigure keyboard-configuration
setupcon
update-initramfs -u


# chrony
apt install -y chrony
grep -qxF "server $TIME_IP iburst" /etc/chrony/chrony.conf || echo "server $TIME_IP iburst" >> /etc/chrony/chrony.conf
systemctl enable chrony
systemctl restart chrony

exit 0

