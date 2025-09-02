#!/bin/bash

# Globals
export DEBIAN_FRONTEND=noninteractive
set -e

# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL Firewall"
echo "-------------------------------------------------------------------------"
echo ""
sleep 1


echo "Remove old rulestate"
iptables -F
iptables -X
systemctl restart docker


echo "Configuring policies"
iptables -P INPUT "$DEFAULT_FW_POLICY_IN"
iptables -P OUTPUT "$DEFAULT_FW_POLICY_OUT"
iptables -P FORWARD "$DEFAULT_FW_POLICY_FWD"

echo "Configuring localhost access"
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A OUTPUT -o lo -j ACCEPT

echo "Configuring default input rules"
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -p icmp -j ACCEPT

echo "Allowing tcp ports: $DEFAULT_FW_PORTS_TCP"
for port in $DEFAULT_FW_PORTS_TCP ; do
    iptables -A INPUT -p tcp --dport "$port" -j ACCEPT
done
echo "Allowing udp ports: $DEFAULT_FW_PORTS_UDP"
for port in $DEFAULT_FW_PORTS_UDP ; do
    iptables -A INPUT -p udp --dport "$port" -j ACCEPT
done


# Store rules
[[ -d /etc/iptables ]] || mkdir -p /etc/iptables
iptables-save > /etc/iptables/rules.v4
cat <<EOF > "/etc/systemd/system/iptables.service"
[Unit]
Description=iptables starter
Requires=docker.service
After=docker.service
[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/etc/iptables
ExecStart=/usr/sbin/iptables-restore rules.v4
ExecStop=/usr/bin/iptables -F
TimeoutStartSec=0
[Install]
WantedBy=multi-user.target
EOF

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
