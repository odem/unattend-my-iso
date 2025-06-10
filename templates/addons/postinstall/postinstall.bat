
echo off
:: VirtIO guest agent
D:\umi\virtio\virtio_win_guest_tools.exe /install /passive /quite /norestart

:: SSH Client and Server
powershell.exe "Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0"
powershell.exe "Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0"
echo D | xcopy /s /Y /I D:\umi\ssh\authorized_keys C:\Users\CFG_USER_OTHER_NAME\.ssh\authorized_keys
echo D | xcopy /s /Y /I D:\umi\ssh\authorized_keys C:\ProgramData\ssh\administrators_authorized_keys
echo D | xcopy /s /Y /I D:\umi\ssh\sshd_config C:\ProgramData\ssh\sshd_config
powershell.exe "Set-Service ssh-agent -StartupType automatic"
powershell.exe "Start-Service ssh-agent"
powershell.exe "Set-Service sshd -StartupType automatic"
powershell.exe "Start-Service sshd"
netsh advfirewall firewall add rule name="Allow SSH (Port 22)" dir=in action=allow protocol=TCP localport=22

:: Misc Options
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v Hidden /t REG_DWORD /d 1 /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v HideFileExt /t REG_DWORD /d 0 /f

:: Firewall (Allow icmp)
netsh advfirewall firewall add rule name="ICMP Allow incoming V4 echo request" protocol="icmpv4:8,any" dir=in action=allow
netsh advfirewall firewall add rule name="ICMP Allow incoming V6 echo request" protocol="icmpv6:8,any" dir=in action=allow

:: Firefox
curl -o C:\Users\CFG_USER_OTHER_NAME\firefoxsetup.msi https://download-installer.cdn.mozilla.net/pub/firefox/releases/136.0.2/win64/de/Firefox%20Setup%20136.0.2.msi
msiexec /package C:\Users\CFG_USER_OTHER_NAME\firefoxsetup.msi /passive

:: Python
curl -o C:\Users\CFG_USER_OTHER_NAME\pythonsetup.exe https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe
C:\Users\CFG_USER_OTHER_NAME\pythonsetup.exe /passive

