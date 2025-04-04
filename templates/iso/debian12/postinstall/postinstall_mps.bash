#!/bin/bash

user=$1
cd /opt || exit 1
git clone https://github.com/odem/mps.git
cd mps || exit 2
sudo -u "root" ./installer/terminal-essentials.bash
sudo -u "root" ./installer/terminal-homedir.bash
sudo -u "root" ./installer/terminal-fonts.bash
sudo -u "root" ./installer/terminal-vim.bash
sudo -u "root" ./installer/terminal-nvim.bash
sudo -u "root" ./installer/desktop-essentials.bash
sudo -u "root" ./installer/desktop-rofi.bash
sudo -u "root" ./installer/desktop-guitools.bash
sudo -u "root" ./installer/desktop-extras.bash
sudo -u "root" ./installer/desktop-spotify.bash
sudo -u "root" ./installer/desktop-qtile.bash
sudo -u "root" ./installer/optimize-grubmenu.bash
sudo -u "root" ./installer/optimize-lightdm.bash
sudo -u "root" ./installer/optimize-tty.bash
sudo -u "root" ./installer/optimize-zram.bash
