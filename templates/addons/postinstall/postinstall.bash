#!/bin/bash

user=CFG_USER_OTHER_NAME
password=CFG_USER_OTHER_PASSWORD

JOBS=("/opt/umi/postinstall/postinstall_apt.bash" "/opt/umi/postinstall/postinstall_locale.bash" "/opt/umi/postinstall/postinstall_ssh.bash" "/opt/umi/postinstall/postinstall_mps.bash")
append_job() {
    if [[ -f $1 ]] ; then
        echo "exists: $1 $2 $3"
        echo "$1" "$2" "$3" >> /firstboot.bash
    else
        echo "Not valid: $1 $2 $3"
    fi
}

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

# preseed-launcher
cat <<EOF > /firstboot.bash
#!/bin/bash
EOF
for str in ${JOBS[@]}; do # Do not quote!
    append_job "$str" "$user" "$password"
done

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
