#!/bin/bash

user=umi

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
/opt/umi/postinstall/postinstall_apt.bash
/opt/umi/postinstall/postinstall_locale.bash
/opt/umi/postinstall/postinstall_ssh.bash
/opt/umi/postinstall/postinstall_mps.bash $user
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



