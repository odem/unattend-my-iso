#!/bin/bash

# Globals
CEPH_VERSION=squid

# Environment variables
POSTINST_PATH=/opt/umi/postinstall
cd "$POSTINST_PATH" || exit 1
envfile=../config/env.bash
if [[ -f "$envfile" ]]; then
    # shellcheck disable=SC1090
    source "$envfile"
fi

CEPH=$(which pveceph)
if [[ "$CEPH" != "" ]]; then
    echo "yJ" | pveceph install -repository no-subscription -version "$CEPH_VERSION"
    # Remove Job From Jobfile
    SERVICE=/firstboot.bash
    if [[ -f "$SERVICE" ]]; then
        filename="$(basename "$0")"
        # shellcheck disable=SC2086
        sed s#$filename##g -i "$SERVICE"
    fi
fi

exit 0
