#!/bin/bash

# Environment variables
envfile=../config/env.bash
if [[ -f "$envfile" ]]; then
    # shellcheck disable=SC1090
    source "$envfile"
fi

# Globals
export DEBIAN_FRONTEND=noninteractive
LOCALESTR=en_US.UTF-8

unset LANG
unset LANGUAGE
unset LC_LANG
unset LC_ALL
locale-gen LANG="$LOCALESTR"
update-locale
    LANG="$LOCALESTR" \
    LANGUAGE="$LOCALESTR" \
    LC_ALL="$LOCALESTR" \
    LC_CTYPE="$LOCALESTR" \
    LC_NUMERIC="$LOCALESTR" \
    LC_TIME="$LOCALESTR" \
    LC_COLLATE="$LOCALESTR" \
    LC_MONETARY="$LOCALESTR" \
    LC_MESSAGES="$LOCALESTR"

echo "LANG=$LOCALESTR">/etc/default/locale
echo "LANGUAGE=$LOCALESTR">/etc/default/locale
echo "LC_ALL=$LOCALESTR">/etc/default/locale
export LANG=$LOCALESTR
export LANGUAGE=$LOCALESTR
locale-gen "$LOCALESTR"
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

