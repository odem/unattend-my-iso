#!/bin/bash
# shellcheck disable=SC1090,1091,2154
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive
SLEEP_BEFORE=5
SLEEP_BETWEEN=1
SLEEP_AFTER=5
RESULT_DIR=/var/log/perf_results
MAX_LOOPS=1000
echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL PERF"
echo "-------------------------------------------------------------------------"
sleep 3

# Update
apt update && apt upgrade -y
sudo apt install -y fio jq sysstat

# systemd unit
cat <<EOF > /etc/systemd/system/perftest.service
[Unit]
Description=Performance Test Script
After=network.target

[Service]
Type=simple
ExecStart=/perftest.bash
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create perftest script
cat <<EOF > /perftest.bash
#!/bin/bash
echo "#########################################################################"
echo "# Unattend-My-Iso: SYSTEMD TARGET PERF"
echo "#########################################################################"

# Clean
rm -rf $RESULT_DIR 2>/dev/null
mkdir -p $RESULT_DIR 2>/dev/null
pkill \$(which fio)

# Iterate Loops
sleep $SLEEP_BEFORE
for counter in \$(seq 1 $MAX_LOOPS); do
    ((counter++))
    echo "---------------------------------------------------------------------"
    echo "- Pertest \$counter"
    echo "---------------------------------------------------------------------"
    /opt/umi/postinstall/fiobench.bash $RESULT_DIR 
    sleep $SLEEP_BETWEEN
    mv $RESULT_DIR/.fiomark.txt $RESULT_DIR/result_\$counter.json
done
sleep $SLEEP_AFTER
EOF

# Enable service
chmod +x /perftest.bash
systemctl daemon-reload
systemctl enable perftest
reboot
# systemctl restart perftest

