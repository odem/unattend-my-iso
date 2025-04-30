#!/bin/bash
# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive
USERNAME="$CFG_USER_OTHER_NAME"
RDP_DIR="$(dirname "$0")"/xrdp

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL TRAFFICGEN"
echo "-------------------------------------------------------------------------"
sleep 3

# Update
apt update && apt upgrade -y

