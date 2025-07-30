
echo off
setlocal

:: Read env config
call D:\umi\config\env.bat
set "SRC_SSH=D:\umi\ssh\"
set "DST_SSH=C:\ProgramData\ssh"
set "DST_USER_OTHER=C:\Users\%CFG_USER_OTHER_NAME%\"

:: SSH Client and Server
powershell.exe "Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0"
powershell.exe "Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0"
mkdir %DST_USER_OTHER%\.ssh
echo D | xcopy /s /Y /I %SRC_SSH%\authorized_keys %DST_USER_OTHER%\.ssh\authorized_keys
echo D | xcopy /s /Y /I %SRC_SSH%\authorized_keys %DST_SSH%\administrators_authorized_keys
REM echo D | xcopy /s /Y /I %SRC_SSH%\sshd_config %DST_SSH%\sshd_config
powershell.exe "Set-Service ssh-agent -StartupType automatic"
powershell.exe "Start-Service ssh-agent"
powershell.exe "Set-Service sshd -StartupType automatic"
powershell.exe "Start-Service sshd"
netsh advfirewall firewall add rule name="Allow SSH (Port 22)" dir=in action=allow protocol=TCP localport=22

endlocal


