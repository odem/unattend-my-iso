

KALI_REPO="deb http://http.kali.org/kali kali-rolling main contrib non-free non-free-firmware"
echo "$KALI_REPO" > /etc/apt/sources.list

apt -y update
apt -y full-upgrade

# apt install kali-linux-everything

apt install kali-linux-core
apt install kali-linux-default
apt install kali-linux-labs

apt install kali-desktop-core
apt install kali-desktop-xfce

apt install kali-tools-fuzzing
apt install kali-tools-information-gathering
apt install kali-tools-vulnerability
apt install kali-tools-web
apt install kali-tools-database
apt install kali-tools-password
apt install kali-tools-reverse-engineering
apt install kali-tools-exploitation
apt install kali-tools-sniffing-spoofing
apt install kali-tools-forensics
apt install kali-tools-reporting



