#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL LOCALE"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1

# Timezone
echo "Europe/Berlin" > /etc/timezone
timedatectl set-timezone Europe/Berlin

# time settings
apt install -y chrony #systemd-resolved
cat <<EOF >/etc/chrony/conf.d/99-local-server.conf
# Set default pool offline
pool 2.debian.pool.ntp.org offline

# Use default 
server $DEFAULT_NIC_0_GW iburst

# listen only locally
bindaddress 127.0.0.1
EOF

# Enable securiyt options
echo "DAEMON_OPTS='-F 1 -4'" > /etc/default/chrony
#mkdir -p /etc/chrony/chrony.d
# echo "bindaddress 127.0.0.1" > /etc/chrony/conf.d/localhost-only.conf
systemctl restart chrony

# Locale
LOCALESTR=$CFG_LOCALE_MULTI
cat <<EOF > /etc/default/locale
LANG=$LOCALESTR
LANGUAGE=$LOCALESTR
LC_ALL=$LOCALESTR
EOF
echo "$CFG_LOCALE_MULTI UTF-8" >> /etc/locale.gen
locale-gen
echo "locales locales/default_environment_locale select $LOCALESTR" \
    | debconf-set-selections
dpkg-reconfigure -f noninteractive locales

# Keyboard
cat <<EOF > /etc/default/keyboard
XKBMODEL="pc105"
XKBLAYOUT="de"
XKBVARIANT="nodeadkeys"
XKBOPTIONS="compose:menu"
BACKSPACE="guess"
EOF
apt-get install -y keyboard-configuration
dpkg-reconfigure -f noninteractive keyboard-configuration

# console
cat <<EOF > /etc/default/console-setup
ACTIVE_CONSOLES="/dev/tty[1-6]"
CHARMAP="UTF-8"
CODESET="Lat15"
FONTFACE="Terminus"
FONTSIZE="8x16"
VIDEOMODE=
EOF
apt-get install -y console-setup
dpkg-reconfigure -f noninteractive console-setup
systemctl enable console-setup.service
systemctl restart console-setup.service
echo ""

# Remove Job From Jobfile
echo "Sucessfully invoked all actions"
SERVICE=/firstboot.bash
if [[ -f "$SERVICE" ]]; then
    filename="$(basename "$0")"
    # shellcheck disable=SC2086
    sed -i "/$filename/d" "$SERVICE"
    echo "Removed job from firstboot script: $(basename "$0")"
fi
echo ""
sleep 1
exit 0
