#!/bin/bash
# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL MPS"
echo "-------------------------------------------------------------------------"
sleep 3

cd "$CFG_ANSWERFILE_HOOK_DIR_TARGET" || exit 1

# user
# sudo ./bootstrap.bash -u "$CFG_USER_OTHER_NAME" -p "$CFG_USER_OTHER_PASSWORD"
# sudo -u "$CFG_USER_OTHER_NAME" ./installer/terminal-essentials.bash
# sudo -u "$CFG_USER_OTHER_NAME" ./installer/terminal-homedir.bash
# sudo -u "$CFG_USER_OTHER_NAME" ./installer/terminal-fonts.bash
# sudo -u "$CFG_USER_OTHER_NAME" ./installer/terminal-vim.bash
# sudo -u "$CFG_USER_OTHER_NAME" ./installer/terminal-nvim.bash
# sudo -u "$CFG_USER_OTHER_NAME" ./installer/desktop-essentials.bash
# sudo -u "$CFG_USER_OTHER_NAME" ./installer/desktop-rofi.bash
# sudo -u "$CFG_USER_OTHER_NAME" ./installer/desktop-guitools.bash
# sudo -u "$CFG_USER_OTHER_NAME" ./installer/desktop-qtile.bash

# root
# sudo -u "root" ./installer/terminal-essentials.bash
# sudo -u "root" ./installer/terminal-homedir.bash
# sudo -u "root" ./installer/terminal-fonts.bash
# sudo -u "root" ./installer/terminal-vim.bash
# sudo -u "root" ./installer/terminal-nvim.bash

# Optimizations
# sudo -u "root" ./installer/optimize-grubmenu.bash
# sudo -u "root" ./installer/optimize-lightdm.bash
