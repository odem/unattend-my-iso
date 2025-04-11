#!/bin/bash

# Usage
usage() {
    echo "Usage: $0 [-d <ceph disk> -n <ceph net prefix>]" 1>&2
    exit 1
}

# Default params (devenv)
# FS_SHAREDNAME=sharedfs
# FS_PUBNAME=pubfs
# FS_USERNAME=userfs
STORAGE_NET=172.19.1
DISKNAME_PRIMARY="/dev/vdb"
RBD_POOL_NAME=hcrbdrep3
CFS_POOL_NAME=hccfsrep3
PG_NUM_DEFAULT=32
PROXMOX_HOST=
PROXMOX_HOST_1=
INIT_CEPH=0
CEPH_VERSION=squid
CEPH_POOL_RBD=rbdrep3
CEPH_POOL_CFS=cfsk2m2
CEPH_MON_LIST="10.10.12.85 10.10.12.87 10.10.12.89 10.10.12.91"
# Read custom config
script_path="$(dirname "$(realpath "$0")")"
source "$script_path"/hostconfig.env
source ~/.bashrc

# Read options
while getopts ":n:d:i:" o; do
    case "$o" in
        d)
            STORAGE_DISK=${OPTARG}
            ;;
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

echo "yJ" | pveceph install -repository no-subscription -version "$CEPH_VERSION"
