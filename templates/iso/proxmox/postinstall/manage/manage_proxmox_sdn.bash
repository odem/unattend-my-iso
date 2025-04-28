#!/bin/bash

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

SDNDIR=/etc/pve/sdn
NAME_ZONE_VLANS=znMain
NAME_VNET_VLAN=advlan
PREFIX_SUBNET_VLAN=10.10.100
TAG_VLAN=1234

echo "Update Zones..."
cat<<EOF > "$SDNDIR/zones.cfg"
vlan: $NAME_ZONE_VLANS
    bridge $BRIDGE0_NAME
    ipam pve
#zone => bridge1
EOF

echo "Update vnets..."
cat<<EOF > "$SDNDIR/vnets.cfg"
vnet: $NAME_VNET_VLAN
    zone $NAME_ZONE_VLANS
    tag $TAG_VLAN
#vnet => $TAG_VLAN
EOF

echo "Update subnets..."
cat<<EOF > "$SDNDIR/subnets.cfg"
subnet: $NAME_ZONE_VLANS-$PREFIX_SUBNET_VLAN.0-24
        vnet $NAME_VNET_VLAN
        snat 1
#subnet => $TAG_VLAN
EOF
sysctl -w net.ipv4.ip_forward=1


# Apply changes
pvesh set /cluster/sdn
sleep 5
pvesh set /cluster/sdn

