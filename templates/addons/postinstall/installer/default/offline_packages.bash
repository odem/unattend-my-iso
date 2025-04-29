#!/bin/bash

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL OFFLINE_PACKAGES"
echo "-------------------------------------------------------------------------"
sleep 1

for file in /opt/umi/packages/* ; do 
    if [[ -f "$file" ]] ; then
        dpkg -i "$file"
    fi
done

# Remove Job From Jobfile
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed s#$filename##g -i "$SERVICE"
fi
exit 0
