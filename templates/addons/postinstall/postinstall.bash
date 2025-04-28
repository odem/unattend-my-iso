#!/bin/bash
# shellcheck disable=SC1090,1091
[[ -f /opt/umi/config/env.bash ]] && source /opt/umi/config/env.bash || exit 1
JOBS=CFG_JOBS_ALL 

# Copy bashrc
if [[ -f /opt/umi/config/.bashrc ]] ; then
    chmod 644 ~/.bashrc
    cat /opt/umi/config/.bashrc > /root/.bashrc
else
    echo ".bashrc not present!"
fi

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

# Create firstboot script
cat <<EOF > /firstboot.bash
#!/bin/bash
echo "#########################################################################"
echo "# Unattend-My-Iso: POSTINSTALL"
echo "#########################################################################"
sleep 3
EOF

# Add Jobs
num_jobs=${#JOBS[@]}
echo "JOBS: ${JOBS[*]}"
echo "Num Jobs: $num_jobs"
for ((i=0; i<num_jobs; i++)); do
    echo "${JOBS[$i]}" >> /firstboot.bash
done

# Add Trailer
cat <<EOF >> /firstboot.bash
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
