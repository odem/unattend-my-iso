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
    announce="$3"
    if [[ "$theuser" != "" ]]; then
        newpass=$(genpw "$length")
        echo "${theuser}:${newpass}" | chpasswd
        if [[ "$announce" == "true" ]] ; then
            printf "Changing password for %18s => %s\n" "$theuser" "$newpass"
        else
            printf "Changing password for %18s => NOT SHOWN!\n" "$theuser"
        fi
    fi
}

echo ""
echo "The script will from now on proceed with deleting config files. "
echo "The script will also change passwords from all accounts including root"
echo "Please confirm before proceeding"
echo ""
read -r -p "Do you want to continue? (y/n): " answer
if [[ "$answer" != "y" ]]; then
    echo "Aborted by user."
    exit 1
fi

# Set password root user
setpw root "$PWSIZE" "true"

# Set password default user
if [[ "$CFG_USER_OTHER_NAME" != "" ]]; then
    setpw "$CFG_USER_OTHER_NAME" "$PWSIZE" "true"
    sudo -u "$CFG_USER_OTHER_NAME" /bin/bash -c "history -c"
fi

# Remove deployment privileges
for i in $(seq 0 $(("${#CFG_DEPLOYMENT_USERS[*]}" - 1))); do
    DEPLOY_NAME="${CFG_DEPLOYMENT_USERS[$i]}"
    echo "-> Grant NOPASSWD privileges to '$DEPLOY_NAME'"
    rm -rf /etc/sudoers.d/"$DEPLOY_NAME"
done
echo ""

# Set passwords additional users
for i in $(seq 0 $(("${#CFG_ADDITIONAL_USERS[*]}" - 1))); do
    ADDITIONAL_NAME="${CFG_ADDITIONAL_USERS[$i]}"
    setpw "$ADDITIONAL_NAME" "$PWSIZE" "false"
    sudo -u "$ADDITIONAL_NAME" /bin/bash -c "history -c"
done
echo ""
echo "Please store the passwords in your password manager!"
echo "They will only be printed once!"
echo ""
echo  "Press ENTER to continue..."
read -r 


# Remove deploymentr users
for i in $(seq 0 $(("${#CFG_DEPLOY_USERS[*]}" - 1))); do
    ADDITIONAL_NAME="${CFG_DEPLOY_USERS[$i]}"
    userdel "$ADDITIONAL_NAME"
    sudo rm -rf /home/"$ADDITIONAL_NAME"
    sudo rm -rf /etc/sudoers.d/"$ADDITIONAL_NAME"
done

# Remove umi config
echo "Removing umi config"
rm -rf "$CFG_ANSWERFILE_HOOK_DIR_TARGET"/config/env.bash

# Remove ssh folder
echo "Removing ssh config"
rm -rf "$CFG_ANSWERFILE_HOOK_DIR_TARGET"/ssh

# Remove user folder
echo "Removing user config"
rm -rf "$CFG_ANSWERFILE_HOOK_DIR_TARGET"/users

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
