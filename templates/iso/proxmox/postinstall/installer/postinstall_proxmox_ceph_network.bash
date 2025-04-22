#!/bin/bash

# Usage
usage() {
    echo "Usage: $0 [-d <ceph disk> -n <ceph net prefix>]" 1>&2
    exit 1
}

RBD_POOL_NAME=hc-rbd-rep3
CFS_POOL_NAME=hc-cfs-rep3
PG_NUM_DEFAULT=32
INIT_CEPH=0

# Environment variables
POSTINST_PATH=/opt/umi/postinstall
cd "$POSTINST_PATH" || exit 1
envfile=../config/env.bash
if [[ -f "$envfile" ]]; then
    # shellcheck disable=SC1090
    source "$envfile"
fi
LEADER_NAME=$DEFAULT_LEADER_PROXMOX

# Read options
while getopts "n:d:i:" o; do
    case "$o" in
        n)
            STORAGE_NET=${OPTARG}
            ;;
        i)
            INIT_CEPH=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

# Bail if requirements are not met
if  [ "$STORAGE_NET" = "" ] ; then
    usage
fi

if [ "$INIT_CEPH" == "0" ] ; then
    if [ "$MANAGE_HOST" == "$LEADER_NAME" ] ; then
        pveceph init --network "${STORAGE_NET}.0/24"
        pveceph mon create
        pveceph mgr create
    else
        pveceph mon create
        pveceph mgr create
    fi
else
    if [ "$MANAGE_HOST" == "$LEADER_NAME" ] ; then
        pveceph pool create "$RBD_POOL_NAME" -pg_num "$PG_NUM_DEFAULT" --add_storages
        pveceph mds create
        pveceph fs create -name "$CFS_POOL_NAME" -add-storage 0  -pg_num "$PG_NUM_DEFAULT"
        cat <<EOF >> /etc/pve/storage.cfg
cephfs: $CFS_POOL_NAME
        path /mnt/pve/$CFS_POOL_NAME
        content iso
        fs-name $CFS_POOL_NAME
EOF
    else
        pveceph mds create
    fi
fi

systemctl restart pvestatd



