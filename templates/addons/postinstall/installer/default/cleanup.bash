#!/bin/bash

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL APT"
echo "-------------------------------------------------------------------------"
sleep 1



length=12
pw_root=$(< /dev/urandom tr -dc 'A-Za-z0-9!@#$%^&*()_+=' | head -c "$length")
pw_maintainer=$(< /dev/urandom tr -dc 'A-Za-z0-9!@#$%^&*()_+=' | head -c "$length")
pw_muser=$(< /dev/urandom tr -dc 'A-Za-z0-9!@#$%^&*()_+=' | head -c "$length")


# Remove Job From Jobfile
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed s#$filename##g -i "$SERVICE"
fi
exit 0
