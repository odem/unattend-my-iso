#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
#set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL FINALIZE"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1

# Password strength
PWSIZE="$CFG_PASSWORD_LENGTH"
CHARSET_PW="$CFG_PASSWORD_CHARSET"
genpw() {
    length=$1
    head /dev/urandom | tr -dc "$CHARSET_PW" | head -c "$length"
}
setpw() {
    theuser="$1"
    length="$2"
    if [[ "$theuser" != "" ]]; then
        newpass=$(genpw "$length")
        printf "Prepare password for %10s => %s\n" "$theuser" "$newpass"
        echo "${theuser}:${newpass}" | chpasswd
    fi
}

# Set password root user
setpw root "$PWSIZE"

# Set password default user
if [[ "$CFG_USER_OTHER_NAME" != "" ]]; then
    setpw "$CFG_USER_OTHER_NAME" "$PWSIZE"
    sudo -u "$CFG_USER_OTHER_NAME" /bin/bash -c "history -c"
fi

# Set passwords additional users
for i in $(seq 0 $(("${#CFG_ADDITIONAL_USERS[*]}" - 1))); do
    ADDITIONAL_NAME="${CFG_ADDITIONAL_USERS[$i]}"
    setpw "$ADDITIONAL_NAME" "$PWSIZE"
    sudo -u "$ADDITIONAL_NAME" /bin/bash -c "history -c"
done
echo ""
echo "Please store the passwords in your password manager!"
echo "They will only be printed once!"
echo ""
echo  "Press ENTER to continue..."
read -r 

# Remove umi config
echo "Removing umi config"
rm -rf /opt/umi/config/env.bash

# Remove ssh folder
echo "Removing ssh config"
rm -rf /opt/umi/ssh

# Remove logs
echo "Removing installer logs"
rm -rf /var/log/installer

# Clear history
echo "Clear history"
history -c

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
