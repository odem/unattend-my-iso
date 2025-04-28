#!/bin/bash

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive

# Sources
cat<< EOF > /etc/apt/sources.list
deb http://deb.debian.org/debian/ bookworm main contrib non-free-firmware
deb http://deb.debian.org/debian/ bookworm-updates main contrib non-free-firmware
#deb http://deb.debian.org/debian/ bookworm-backports main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free-firmware
EOF

# update and install essentials
apt-get update -y && apt-get upgrade -y

# Remove Job From Jobfile
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed s#$filename##g -i "$SERVICE"
fi
exit 0
