#!/bin/bash


# Environment variables
envfile=../config/env.bash
if [[ -f "$envfile" ]]; then
    # shellcheck disable=SC1090
    source "$envfile"
fi
JOBS=CFG_JOBS_ALL 

# Copy bashrc
if [[ -f /opt/umi/config/.bashrc ]] ; then
    cp /opt/umi/config/.bashrc ~
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
