#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
LOCALESTR=en_US.UTF-8

# bashrc
cp /opt/umi/postinstall/.bashrc /root/.bashrc

# sudo efibootmgr --create --disk /dev/vda --part 1 --loader '\\EFI\\debian\\grubx64.efi' --label "DebianNew" --verbose

unset LANG
unset LANGUAGE
unset LC_LANG
unset LC_ALL
locale-gen LANG="$LOCALESTR"
update-locale
    LANG="$LOCALESTR" \
    LANGUAGE="$LOCALESTR" \
    LC_LANG="$LOCALESTR" \
    LC_ALL="$LOCALESTR" \
    LC_CTYPE="$LOCALESTR" \
    LC_NUMERIC="$LOCALESTR" \
    LC_TIME="$LOCALESTR" \
    LC_COLLATE="$LOCALESTR" \
    LC_MONETARY="$LOCALESTR" \
    LC_MESSAGES="$LOCALESTR" \
    LC_PAPER="$LOCALESTR" \
    LC_NAME="$LOCALESTR" \
    LC_ADDRESS="$LOCALESTR" \
    LC_TELEPHONE="$LOCALESTR" \
    LC_MEASUREMENT="$LOCALESTR" \
    LC_IDENTIFICATION="$LOCALESTR" \

echo "LANG=$LOCALESTR">/etc/default/locale
echo "LANGUAGE=$LOCALESTR">/etc/default/locale
echo "LC_ALL=$LOCALESTR">/etc/default/locale
source /root/.bashrc

# Locales
export LANG=$LOCALESTR
export LANGUAGE=$LOCALESTR
locale-gen "$LOCALESTR"
echo "locales locales/default_environment_locale select $LOCALESTR" \
    | debconf-set-selections
dpkg-reconfigure -f noninteractive locales

cat <<EOF > /etc/default/keyboard
XKBMODEL="pc105"
XKBLAYOUT="de"
XKBVARIANT="nodeadkeys"
XKBOPTIONS="compose:menu"
BACKSPACE="guess"
EOF
dpkg-reconfigure -f noninteractive keyboard-configuration
systemctl enable console-setup.service
systemctl restart console-setup.service

# Sources
cat<< EOF > /etc/apt/sources.list
deb http://deb.debian.org/debian/ bookworm main contrib non-free-firmware
deb http://deb.debian.org/debian/ bookworm-updates main contrib non-free-firmware
deb http://deb.debian.org/debian/ bookworm-backports main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free-firmware
EOF
apt-get update -y && apt-get upgrade -y && apt-get install -y \
    sudo psmisc bsdmainutils ntp lsb-release curl gnupg  \
     traceroute iftop sysstat bridge-utils net-tools tcpdump nmap \
    git vim make kitty bc

# SSH
if [[ -f /opt/postinstall/ssh/id_rsa.pub ]] ; then
    mkdir -p /root/.ssh
    cp /opt/postinstall/ssh/id_rsa* /root/.ssh/
    chmod 0600 /root/.ssh/id_rsa*
fi

# Authorization
if [[ -f /opt/postinstall/ssh/authorized_keys ]] ; then
    cp /opt/postinstall/ssh/authorized_keys /root/.ssh/authorized_keys
fi

# SSHD
if [[ -f /opt/postinstall/ssh/sshd_config ]] ; then
    cp /opt/postinstall/ssh/sshd_config /etc/ssh/sshd_config
fi
systemctl enable ssh
systemctl restart ssh

# systemd unit
cat <<EOF > /etc/systemd/system/firstboot.service
[Unit]
Description=Firstboot script
Before=getty@tty1.service
[Service]
Type=oneshot
ExecStart=/firstboot.bash
StandardInput=tty
StandardOutput=tty
StandardError=tty
[Install]
WantedBy=getty.target
EOF

# preseed-launcher
cat <<EOF > /firstboot.bash
#!/bin/bash
/opt/umi/postinstall/postinstall_mps.bash
systemctl disable firstboot.service
rm -rf /etc/systemd/service/firstboot.service
rm -rf /firstboot.bash
shutdown -r now
exit 0
EOF

# enable service
chmod +x /firstboot.bash
systemctl daemon-reload
systemctl enable firstboot



