#!/bin/bash

echo "All Installer"

/usr/local/bin/install-apt.bash
/usr/local/bin/install-offline-packages.bash
/usr/local/bin/install-networking.bash
/usr/local/bin/install-user-live.bash
/usr/local/bin/install-zfs.bash
/usr/local/bin/install-debian.bash
