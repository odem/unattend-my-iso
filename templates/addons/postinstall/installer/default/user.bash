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
if [[ -d "$CFG_ANSWERFILE_HOOK_DIR_TARGET"/users/root/ ]] ; then
    cp -r "$CFG_ANSWERFILE_HOOK_DIR_TARGET"/users/root/. /root/
    if [[ -f "$CFG_ANSWERFILE_HOOK_DIR_TARGET/ssh/authorized_keys" ]] ; then
        cat "$CFG_ANSWERFILE_HOOK_DIR_TARGET/ssh/authorized_keys" \
            > /root/.ssh/authorized_keys
    fi
    chmod 700 -R /root/
    chown "root:root" -R /root
fi

# Configure default user
if [[ "$CFG_USER_OTHER_NAME" != "" ]]; then
    echo "-> Prepare default user '$CFG_USER_OTHER_NAME'"
    if [[ -d "$CFG_ANSWERFILE_HOOK_DIR_TARGET/users/$CFG_USER_OTHER_NAME/" ]] ; then
        cp -r "$CFG_ANSWERFILE_HOOK_DIR_TARGET/users/$CFG_USER_OTHER_NAME/". "/home/$CFG_USER_OTHER_NAME"
    fi
    if [[ -f "$CFG_ANSWERFILE_HOOK_DIR_TARGET/ssh/authorized_keys" ]] ; then
        cat "$CFG_ANSWERFILE_HOOK_DIR_TARGET/ssh/authorized_keys" \
            > "/home/$CFG_USER_OTHER_NAME"/.ssh/authorized_keys
    fi
    chmod 700 -R "/home/$CFG_USER_OTHER_NAME/"
    chown "$CFG_USER_OTHER_NAME:$CFG_USER_OTHER_NAME" -R "/home/$CFG_USER_OTHER_NAME/"
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
    if [[ -d "$CFG_ANSWERFILE_HOOK_DIR_TARGET/users/$ADDITIONAL_NAME/" ]] ; then
       cp -r "$CFG_ANSWERFILE_HOOK_DIR_TARGET/users/$ADDITIONAL_NAME/". "/home/$ADDITIONAL_NAME"
    fi
    if [[ -f "$CFG_ANSWERFILE_HOOK_DIR_TARGET/ssh/authorized_keys" ]] ; then
        cat "$CFG_ANSWERFILE_HOOK_DIR_TARGET/ssh/authorized_keys" \
            > "/home/$ADDITIONAL_NAME"/.ssh/authorized_keys
    fi
    chmod 700 -R "/home/$ADDITIONAL_NAME/"
    chown "$ADDITIONAL_NAME:$ADDITIONAL_NAME" -R "/home/$ADDITIONAL_NAME/"
done

# Configure sudo users
for i in $(seq 0 $(("${#CFG_SUDO_USERS[*]}" - 1))); do
    SUDO_NAME="${CFG_SUDO_USERS[$i]}"
    echo "-> Prepare sudo user '$SUDO_NAME'"
    /sbin/usermod -aG sudo "$SUDO_NAME"
    echo "-> Grant NOPASSWD privileges to '$SUDO_NAME'"
    cat <<EOF > /etc/sudoers.d/"$SUDO_NAME"
$SUDO_NAME ALL=(ALL) NOPASSWD: ALL
EOF
done
echo ""

# Configure admin users
for i in $(seq 0 $(("${#CFG_ADMIN_USERS[*]}" - 1))); do
    ADDITIONAL_USER="${CFG_ADMIN_USERS[$i]}"
    echo "-> Prepare admin user '$ADDITIONAL_USER'"
    /sbin/usermod -aG "$CFG_ADMIN_GROUP_NAME" "$ADDITIONAL_USER"
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
