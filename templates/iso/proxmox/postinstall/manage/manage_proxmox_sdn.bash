#!/bin/bash

# Vars
SDNDIR=/etc/pve/sdn

# Vlans
NAME_ZONE_VLANS=znKDN
PREFIX_BRIDGE_VLANS=10.10.25

# Vlan 1728
NAME_VNET_VLAN1728=adpilot
PREFIX_SUBNET_VLAN1728=10.10.100
TAG_VLAN1728=1728

# Read custom config
script_path="$(dirname "$(realpath "$0")")"
source "$script_path"/hostconfig.env

if grep -q "iface $BRIDGE1_NAME" /etc/network/interfaces; then
    echo "$BRIDGE1_NAME exists. Skipping bridge setup..."
else
    cat<<EOF >> /etc/network/interfaces
auto $BRIDGE1_NAME
iface $BRIDGE1_NAME inet manual
    bridge_ports $BOND1_NAME
    bridge_stp off
    bridge_fd 0
EOF
fi

if grep -q "iface $INTERFACE_VLAN_STORAGE" /etc/network/interfaces; then
    echo "$INTERFACE_VLAN_STORAGE exists. Skipping bridge setup..."
else
    cat<<EOF >> /etc/network/interfaces
auto $INTERFACE_VLAN_STORAGE
iface $INTERFACE_VLAN_STORAGE inet static
    address $STORAGE_IP/24
    vlan-raw-device $BRIDGE1_NAME
#NIC 1 Storage
EOF
fi

if grep -q "iface $INTERFACE_VLAN_HEARTBEAT" /etc/network/interfaces; then
    echo "$INTERFACE_VLAN_HEARTBEAT exists. Skipping bridge setup..."
else
    cat<<EOF >> /etc/network/interfaces
auto $INTERFACE_VLAN_HEARTBEAT
iface $INTERFACE_VLAN_HEARTBEAT inet static
    address $HB_IP/24
    vlan-raw-device $BRIDGE1_NAME
#NIC 1 Heartbeat
EOF
fi
systemctl restart networking

echo "Update Zones..."
cat<<EOF > "$SDNDIR/zones.cfg"
vlan: $NAME_ZONE_VLANS
    bridge $BRIDGE0_NAME
    ipam pve
#zone => bridge1
EOF

echo "Update vnets..."
cat<<EOF > "$SDNDIR/vnets.cfg"
vnet: $NAME_VNET_VLAN1728
    zone $NAME_ZONE_VLANS
    tag $TAG_VLAN1728
#vnet => 1728
EOF

echo "Update subnets..."
cat<<EOF > "$SDNDIR/subnets.cfg"
subnet: $NAME_ZONE_VLANS-$PREFIX_SUBNET_VLAN1728.0-24
        vnet $NAME_VNET_VLAN1728
        snat 1
#subnet => 1728
EOF
sysctl -w net.ipv4.ip_forward=1


# Apply changes
pvesh set /cluster/sdn
sleep 5
pvesh set /cluster/sdn

