#!/bin/bash

echo "All Installer"

/opt/umi/postinstall/installer/default/offline_packages.bash
/opt/umi/postinstall/installer/default/hostnames.bash
/opt/umi/postinstall/installer/default/hostnet_dhcp.bash
/opt/umi/postinstall/installer/default/apt.bash
# /usr/local/bin/install-zfs.bash
# /usr/local/bin/install-debian.bash
# /usr/local/bin/install-user-live.bash
