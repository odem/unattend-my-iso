#!/bin/bash

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive


echo "Reading nodes from config (Ceph Management)..."
if [[ "$NODES_CEPH_MANAGE_NAME" != "" ]]; then
    IFS=',' read -ra MEMBERS_CEPH_MANAGE_NAME <<< "$NODES_CEPH_MANAGE_NAME"
fi
if [[ "$NODES_CEPH_MANAGE_FQDN" != "" ]]; then
    IFS=',' read -ra MEMBERS_CEPH_MANAGE_FQDN <<< "$NODES_CEPH_MANAGE_FQDN"
fi
if [[ "$NODES_CEPH_MANAGE_IP" != "" ]]; then
    IFS=',' read -ra MEMBERS_CEPH_MANAGE_IP <<< "$NODES_CEPH_MANAGE_IP"
fi
echo "Reading nodes from config (Ceph Heartbeat)..."
if [[ "$NODES_CEPH_MANAGE_NAME" != "" ]]; then
    IFS=',' read -ra MEMBERS_CEPH_HB_NAME <<< "$NODES_CEPH_HB_NAME"
fi
if [[ "$NODES_CEPH_HB_FQDN" != "" ]]; then
    IFS=',' read -ra MEMBERS_CEPH_HB_FQDN <<< "$NODES_CEPH_HB_FQDN"
fi
if [[ "$NODES_CEPH_HB_IP" != "" ]]; then
    IFS=',' read -ra MEMBERS_CEPH_HB_IP <<< "$NODES_CEPH_HB_IP"
fi
echo "Reading nodes from config (Ceph Storage)..."
if [[ "$NODES_CEPH_MANAGE_NAME" != "" ]]; then
    IFS=',' read -ra MEMBERS_CEPH_STORAGE_NAME <<< "$NODES_CEPH_STORAGE_NAME"
fi
if [[ "$NODES_CEPH_STORAGE_FQDN" != "" ]]; then
    IFS=',' read -ra MEMBERS_CEPH_STORAGE_FQDN <<< "$NODES_CEPH_STORAGE_FQDN"
fi
if [[ "$NODES_CEPH_STORAGE_IP" != "" ]]; then
    IFS=',' read -ra MEMBERS_CEPH_STORAGE_IP <<< "$NODES_CEPH_STORAGE_IP"
fi

echo "Reading nodes from config (Proxmox Management)..."
if [[ "$NODES_PROX_MANAGE_NAME" != "" ]]; then
    IFS=',' read -ra MEMBERS_PROX_MANAGE_NAME <<< "$NODES_PROX_MANAGE_NAME"
fi
if [[ "$NODES_PROX_MANAGE_FQDN" != "" ]]; then
    IFS=',' read -ra MEMBERS_PROX_MANAGE_FQDN <<< "$NODES_PROX_MANAGE_FQDN"
fi
if [[ "$NODES_PROX_MANAGE_IP" != "" ]]; then
    IFS=',' read -ra MEMBERS_PROX_MANAGE_IP <<< "$NODES_PROX_MANAGE_IP"
fi
echo "Reading nodes from config (Proxmox Heartbeat)..."
if [[ "$NODES_PROX_MANAGE_NAME" != "" ]]; then
    IFS=',' read -ra MEMBERS_PROX_HB_NAME <<< "$NODES_PROX_HB_NAME"
fi
if [[ "$NODES_PROX_HB_FQDN" != "" ]]; then
    IFS=',' read -ra MEMBERS_PROX_HB_FQDN <<< "$NODES_PROX_HB_FQDN"
fi
if [[ "$NODES_PROX_HB_IP" != "" ]]; then
    IFS=',' read -ra MEMBERS_PROX_HB_IP <<< "$NODES_PROX_HB_IP"
fi
echo "Reading nodes from config (Proxmox Storage)..."
if [[ "$NODES_PROX_MANAGE_NAME" != "" ]]; then
    IFS=',' read -ra MEMBERS_PROX_STORAGE_NAME <<< "$NODES_PROX_STORAGE_NAME"
fi
if [[ "$NODES_PROX_STORAGE_FQDN" != "" ]]; then
    IFS=',' read -ra MEMBERS_PROX_STORAGE_FQDN <<< "$NODES_PROX_STORAGE_FQDN"
fi
if [[ "$NODES_PROX_STORAGE_IP" != "" ]]; then
    IFS=',' read -ra MEMBERS_PROX_STORAGE_IP <<< "$NODES_PROX_STORAGE_IP"
fi

# Hostname
echo "$MANAGE_HOST" > /etc/hostname
hostname -b "$MANAGE_HOST"

# Common hosts
cat <<EOF > /etc/hosts
# local
127.0.0.1 localhost
127.0.1.1 $MANAGE_HOST $MANAGE_HOST.$MANAGE_DOMAIN 

# ipv6
# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF

if [[ ${#MEMBERS_PROX_MANAGE_NAME[*]} -gt 0 ]] ; then
    echo "" >> /etc/hosts
    echo "# Hosts Proxmox (Management)" >> /etc/hosts
    for i in $(seq 0 $(("${#MEMBERS_PROX_MANAGE_NAME[*]}" - 1))); do
        NEWLINE="${MEMBERS_PROX_MANAGE_IP[$i]} ${MEMBERS_PROX_MANAGE_NAME[$i]} ${MEMBERS_PROX_MANAGE_FQDN[$i]}"
        echo "$NEWLINE" >> /etc/hosts
    done
    echo "# Hosts Proxmox (Heartbeat)" >> /etc/hosts
    for i in $(seq 0 $(("${#MEMBERS_PROX_HB_NAME[*]}" - 1))); do
        NEWLINE="${MEMBERS_PROX_HB_IP[$i]} ${MEMBERS_PROX_HB_NAME[$i]} ${MEMBERS_PROX_HB_FQDN[$i]}"
        echo "$NEWLINE" >> /etc/hosts
    done
    echo "# Hosts Proxmox (Storage)" >> /etc/hosts
    for i in $(seq 0 $(("${#MEMBERS_PROX_STORAGE_NAME[*]}" - 1))); do
        NEWLINE="${MEMBERS_PROX_STORAGE_IP[$i]} ${MEMBERS_PROX_STORAGE_NAME[$i]} ${MEMBERS_PROX_STORAGE_FQDN[$i]}"
        echo "$NEWLINE" >> /etc/hosts
    done
fi
if [[ ${#MEMBERS_CEPH_MANAGE_NAME[*]} -gt 0 ]] ; then
    echo "" >> /etc/hosts
    echo "# Hosts Ceph (Management)" >> /etc/hosts
    for i in $(seq 0 $(("${#MEMBERS_CEPH_MANAGE_NAME[*]}" - 1))); do
        NEWLINE="${MEMBERS_CEPH_MANAGE_IP[$i]} ${MEMBERS_CEPH_MANAGE_NAME[$i]} ${MEMBERS_CEPH_MANAGE_FQDN[$i]}"
        echo "$NEWLINE" >> /etc/hosts
    done
    echo "# Hosts Ceph (Heartbeat)" >> /etc/hosts
    for i in $(seq 0 $(("${#MEMBERS_CEPH_HB_NAME[*]}" - 1))); do
        NEWLINE="${MEMBERS_CEPH_HB_IP[$i]} ${MEMBERS_CEPH_HB_NAME[$i]} ${MEMBERS_CEPH_HB_FQDN[$i]}"
        echo "$NEWLINE" >> /etc/hosts
    done
    echo "# Hosts Ceph (Storage)" >> /etc/hosts
    for i in $(seq 0 $(("${#MEMBERS_CEPH_STORAGE_NAME[*]}" - 1))); do
        NEWLINE="${MEMBERS_CEPH_STORAGE_IP[$i]} ${MEMBERS_CEPH_STORAGE_NAME[$i]} ${MEMBERS_CEPH_STORAGE_FQDN[$i]}"
        echo "$NEWLINE" >> /etc/hosts
    done
fi

# Remove Job From Jobfile
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed s#$filename##g -i "$SERVICE"
fi
exit 0
