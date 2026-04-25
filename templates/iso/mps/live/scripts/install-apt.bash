#!/bin/bash

# shellcheck disable=SC1091
source /etc/os-release
CODENAME=$VERSION_CODENAME

# Sources
cat<< EOF > /etc/apt/sources.list
deb http://deb.debian.org/debian/ $CODENAME main contrib non-free-firmware
deb-src http://deb.debian.org/debian/ $CODENAME main contrib non-free-firmware
deb http://deb.debian.org/debian/ $CODENAME-updates main contrib non-free-firmware
deb-src http://deb.debian.org/debian/ $CODENAME-updates main contrib non-free-firmware
#deb http://deb.debian.org/debian/ $CODENAME-backports main contrib non-free non-free-firmware
#deb-src http://deb.debian.org/debian/ $CODENAME-backports main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security $CODENAME-security main contrib non-free-firmware
deb-src http://security.debian.org/debian-security $CODENAME-security main contrib non-free-firmware
EOF
apt-get update -y
apt-get install -f -y
apt-get upgrade -y
apt-get install -y apt-utils
apt-get autoremove

