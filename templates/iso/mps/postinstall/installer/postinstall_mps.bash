#!/bin/bash
# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL MPS"
echo "-------------------------------------------------------------------------"
sleep 3

cd "$CFG_ANSWERFILE_HOOK_DIR_TARGET" || exit 1

install_user() {
    NAME=$1
    sudo -u "$NAME" ./installer/terminal-essentials.bash
    sudo -u "$NAME" ./installer/terminal-homedir.bash
    sudo -u "$NAME" ./installer/terminal-fonts.bash
    sudo -u "$NAME" ./installer/terminal-vim.bash
    sudo -u "$NAME" ./installer/terminal-nvim.bash
    sudo -u "$NAME" ./installer/desktop-essentials.bash
    sudo -u "$NAME" ./installer/desktop-rofi.bash
    sudo -u "$NAME" ./installer/desktop-guitools.bash
    sudo -u "$NAME" ./installer/desktop-qtile.bash
}

# root
install_user "root"

# other user
install_user "$CFG_USER_OTHER_NAME"

# additional users
for i in $(seq 0 $(("${#CFG_ADDITIONAL_USERS[*]}" - 1))); do
    ADDITIONAL_USER="${CFG_ADDITIONAL_USERS[$i]}"
    sudo ./bootstrap.bash -u "$ADDITIONAL_USER" -p "${ADDITIONAL_USER}pass"
    install_user "$ADDITIONAL_USER"
done

# Optimizations
sudo -u "root" ./installer/optimize-grubmenu.bash
sudo -u "root" ./installer/optimize-lightdm.bash
