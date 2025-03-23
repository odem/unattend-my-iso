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
sudo -u "root" ./installer/optimize-tty.bash
sudo -u "root" ./installer/optimize-zram.bash
sudo -u "root" ./installer/optimize-grubmenu.bash
sudo -u "root" ./installer/optimize-lightdm.bash


apt install -y kmscon
mkdir /etc/kmscon
cat <<EOF > /etc/kmscon/kmscon.conf
font-size=14
xkb-repeat-delay=100
xkb-repeat-rate=100
EOF

cp -r /opt/umi/theme /boot/grub
grep "GRUB_GFXMODE=" /etc/default/grub >/dev/null 2>&1 && sed -i '/GRUB_GFXMODE=/d' /etc/default/grub
echo "GRUB_GFXMODE=\"1280x800x32\"" >> /etc/default/grub
grep "GRUB_THEME=" /etc/default/grub >/dev/null 2>&1 && sed -i '/GRUB_THEME=/d' /etc/default/grub
echo "GRUB_THEME=\"/boot/grub/theme/theme.txt\"" >> /etc/default/grub
update-grub
