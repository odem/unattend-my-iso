#!/bin/bash

user=$1
password=$2

cd /opt || exit 1
git clone https://github.com/odem/mps.git
cd mps || exit 2

# user
sudo ./bootstrap.bash -u "$user" -p "$password"
sudo -u "$user" ./installer/terminal-essentials.bash
sudo -u "$user" ./installer/terminal-homedir.bash
sudo -u "$user" ./installer/terminal-fonts.bash
sudo -u "$user" ./installer/terminal-vim.bash
sudo -u "$user" ./installer/terminal-nvim.bash
# sudo -u "$user" ./installer/desktop-essentials.bash
# sudo -u "$user" ./installer/desktop-rofi.bash
# sudo -u "$user" ./installer/desktop-guitools.bash
# sudo -u "$user" ./installer/desktop-extras.bash
# sudo -u "$user" ./installer/desktop-spotify.bash
# sudo -u "$user" ./installer/desktop-qtile.bash
#
# # root
# sudo -u "root" ./installer/terminal-essentials.bash
# sudo -u "root" ./installer/terminal-homedir.bash
# sudo -u "root" ./installer/terminal-fonts.bash
# sudo -u "root" ./installer/terminal-vim.bash
# sudo -u "root" ./installer/terminal-nvim.bash
#
# Optimizations
sudo -u "root" ./installer/optimize-grubmenu.bash
sudo -u "root" ./installer/optimize-lightdm.bash
# sudo -u "root" ./installer/optimize-tty.bash
# sudo -u "root" ./installer/optimize-zram.bash
sudo -u "root" ./installer/optimize-ramdisks.bash
