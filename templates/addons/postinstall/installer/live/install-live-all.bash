#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
# set -eo pipefail

# Read kernel or exit
KVERSION="$1"
echo "Kernel version was: '$KVERSION'"
[[ -n "$KVERSION" ]] || exit 1

# Install UMI defaults
/opt/umi/postinstall/installer/default/offline_packages.bash
/opt/umi/postinstall/installer/default/hostnet_dhcp.bash
/opt/umi/postinstall/installer/default/apt.bash
/opt/umi/postinstall/installer/default/locale.bash

# Install live installers
/opt/umi/postinstall/installer/live/install-live-essentials.bash
/opt/umi/postinstall/installer/live/install-live-user.bash
/opt/umi/postinstall/installer/default/shell.bash
