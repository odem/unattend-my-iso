#!/bin/bash

DEVICES=("/dev/sdb" "/dev/sdc" "/dev/sdd" "/dev/sde" "/dev/sdf" "/dev/sdg" "/dev/sdh")
DISKNAME_CEPH_DEFAULT=""

# Usage
usage() {
    echo "Usage: $0 [-d <ceph disk>]" 1>&2
    exit 1
}

# Environment variables
POSTINST_PATH=/opt/umi/postinstall
cd "$POSTINST_PATH" || exit 1
envfile=../config/env.bash
if [[ -f "$envfile" ]]; then
    # shellcheck disable=SC1090
    source "$envfile"
fi

# Read options
while getopts "d:" o; do
    case "$o" in
        d)
            DISKNAME_CEPH_DEFAULT=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))


if [ "$DISKNAME_CEPH_DEFAULT" == "" ]; then
    for DEVICE in "${DEVICES[@]}"; do
        pveceph osd create "$DEVICE"
    done
else
    pveceph osd create "$DISKNAME_CEPH_DEFAULT"

fi


