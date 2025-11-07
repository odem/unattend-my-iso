#!/bin/bash

# Default folders and filenames
DIR_OUT=configdrive
DIR_OPENSTACK=openstack
DIR_ISO="$DIR_OUT"/"$DIR_OPENSTACK"
DIR_CFG="$DIR_ISO"/latest
ISO_OUT=configdrive.iso

# CI Config
CI_USERPASS=aaa12345678
CI_ADMINPASS=aaa87654321
CI_USERNAME=testuser
CI_ADMINNAME=testadmin
CI_HOSTNAME=cihost
CI_GROUP_ADMIN="Administratoren"
CI_GROUP_USERS="Benutzer"
CI_UUID="12345678-1234-5678-1234-567812345678"
CI_REG='\SOFTWARE\Cloudbase Solutions\Cloudbase-Init\'

# Create folders
mkdir -p "$DIR_CFG"

# Create CI Data
cat <<EOF > "$DIR_CFG"/meta_data.json
{
  "uuid": "${CI_UUID}",
  "hostname": "${CI_HOSTNAME}"
}
EOF
cat <<EOF > "$DIR_CFG"/user_data
#cloud-config
users:
  -
    name: ${CI_ADMINNAME}
    gecos: 'CI ${CI_ADMINNAME}'
    primary_group: ${CI_GROUP_ADMIN}
    groups: ${CI_GROUP_ADMIN}
    passwd: ${CI_ADMINPASS}
    inactive: False
    expiredate: 2099-10-01
  -
    name: ${CI_USERNAME}
    gecos: 'CI ${CI_USERNAME}'
    primary_group: ${CI_GROUP_USERS}
    groups: ${CI_GROUP_USERS}
    passwd: ${CI_USERPASS}
    inactive: False
    expiredate: 2099-10-01
write_files:
  - path: C:/Users/${CI_USERNAME}/autostart.ps1
    content: |
      Write-Output "This script was run by cloudbase-init" Out-File -FilePath C:/Users/${CI_USERNAME}/script-output.txt
      Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" -Name "CIAutostart" -Value "powershell.exe -ExecutionPolicy Bypass -File C:/Users/${CI_USERNAME}/autostart.ps1" 
      cd "C:\\Program Files\\Cloudbase Solutions\\Cloudbase-Init\\Python\\Scripts\\cloudbase-init.exe"
      ./cloudbase-init.exe --config-file ./cloudbase-init.conf --debug
      Remove-ItemProperty -Path "HKLM:\\${CI_REG}\\${CI_UUID}\\Plugins" -Name "UserDataPlugin"
runcmd:
  - ['powershell.exe', "-ExecutionPolicy", "Bypass","-File", "C:/Users/${CI_USERNAME}/autostart.ps1"]
EOF

# Create CI Image
rm -rf "$ISO_OUT"
genisoimage -output "$ISO_OUT" \
    -volid config-2 -joliet -rock \
    -graft-points openstack="$DIR_ISO"

