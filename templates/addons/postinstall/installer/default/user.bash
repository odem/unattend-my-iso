#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

PWGEN="$CFG_PASSWORD_GENERATE"
PWSIZE="$CFG_PASSWORD_LENGTH"
CHARSET_PW="$CFG_PASSWORD_CHARSET"

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL USER"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1

genpw() {
    length=$1
    head /dev/urandom | tr -dc "$CHARSET_PW" | head -c "$length"
}

# Configure root user
echo "-> Prepare user 'root'"
# TODO: What to do here?

# Configure default user
if [[ "$CFG_USER_OTHER_NAME" != "" ]]; then
    echo "-> Prepare default user '$CFG_USER_OTHER_NAME'"
    /sbin/usermod -aG sudo "$CFG_USER_OTHER_NAME"
fi
# Configure additional users
for i in $(seq 0 $(("${#CFG_ADDITIONAL_USERS[*]}" - 1))); do
    ADDITIONAL_NAME="${CFG_ADDITIONAL_USERS[$i]}"
    echo "-> Prepare additional user '$ADDITIONAL_NAME'"
    # /sbin/adduser --disabled-password --gecos '' "$ADDITIONAL_NAME"
    if [[ $PWGEN -eq 1 ]] ; then
        newpass=$(genpw "$PWSIZE")
    else
        newpass="${ADDITIONAL_NAME}pass"
    fi
    echo "${ADDITIONAL_NAME}:${newpass}" | chpasswd
    cp /opt/umi/config/.bashrc /home/"$ADDITIONAL_NAME"
done

# Configure sudo users
for i in $(seq 0 $(("${#CFG_SUDO_USERS[*]}" - 1))); do
    ADDITIONAL_NAME="${CFG_SUDO_USERS[$i]}"
    echo "-> Prepare sudo user '$ADDITIONAL_NAME'"
    /sbin/usermod -aG sudo "$ADDITIONAL_NAME"
done
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
