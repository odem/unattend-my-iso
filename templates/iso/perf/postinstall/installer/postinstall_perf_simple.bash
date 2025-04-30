#!/bin/bash
# shellcheck disable=SC1090,1091,2154
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1

# Globals
export DEBIAN_FRONTEND=noninteractive
SLEEP_BEFORE=1
SLEEP_BETWEEN=1
SLEEP_AFTER=1
RESULT_DIR=/var/log/perf_results
MAX_LOOPS=1000
FIO_SIZE=256
FIO_LOOPS=5
echo "-------------------------------------------------------------------------"
echo "- Unattend-My-Iso: POSTINSTALL PERF"
echo "-------------------------------------------------------------------------"
sleep 3

# Update
apt update && apt upgrade -y
sudo apt install -y fio jq sysstat
mkdir -p $RESULT_DIR 2>/dev/null

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
# StandardOutput=append:$RESULT_DIR/perftest.log
# StandardError=append:$RESULT_DIR/perftest.log

# Create perftest script
cat <<EOF > /perftest.bash
#!/bin/bash
echo "#########################################################################"
echo "# Unattend-My-Iso: SYSTEMD TARGET PERF_SIMPLE"
echo "#########################################################################"

# Clean
rm -rf $RESULT_DIR #2>/dev/null
mkdir -p $RESULT_DIR #2>/dev/null
pkill \$(which fio)
echo "Cleaned"

# Iterate loops
sleep $SLEEP_BEFORE
for counter in \$(seq 1 $MAX_LOOPS); do
    echo "---------------------------------------------------------------------"
    echo "- Perftest \$counter"
    echo "---------------------------------------------------------------------"
    fio --loops=$FIO_LOOPS --size=${FIO_SIZE}m --filename="$RESULT_DIR/.fiomark.tmp" \
      --stonewall --ioengine=libaio --direct=1 --zero_buffers=0 --output-format=json \
      --name=Seqread --bs=${FIO_SIZE}m --iodepth=1 --numjobs=1 --rw=read \
      --name=Seqwrite --bs=${FIO_SIZE}m --iodepth=1 --numjobs=1 --rw=write \
      2>&1 > $RESULT_DIR/perftest.log
    sleep $SLEEP_BETWEEN
    cat $RESULT_DIR/perftest.log
    mv $RESULT_DIR/perftest.log $RESULT_DIR/result_\$counter.json
done
sleep $SLEEP_AFTER
echo "Done"
exit 0
EOF

# Enable service
chmod +x /perftest.bash
systemctl daemon-reload
systemctl enable perftest

