
echo off
setlocal

:: Read env config
call D:\umi\config\env.bat
set "SRC_SSH=D:\umi\ssh\"
set "SRC_SSH_ALL=D:\umi\ssh\authorized_keys"
set "SRC_SSH_USER=D:\umi\users\%CFG_USER_OTHER_NAME%\.ssh\authorized_keys"
set "DST_SSH_USER="
set "DST_SSH=C:\ProgramData\ssh"
set "DST_USER_OTHER=%DST_USER_OTHER%\.ssh\authorized_keys"

:: SSH Client and Server
powershell.exe "Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0"
powershell.exe "Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0"
mkdir %DST_USER_OTHER%\.ssh

if exist "%SRC_SSH_ALL%" if exist "%SRC_SSH_USER%" (
    copy /b "%SRC_SSH_ALL%" + "%SRC_SSH_USER%" "%DST_USER_OTHER%"
) else (
    echo "Found only one ssh auth file"
    if exist "%SRC_SSH_ALL%" (
        echo D | xcopy /s /Y /I %SRC_SSH_ALL% %DST_USER_OTHER%
    ) 
)
if exist "%DST_USER_OTHER%" (
    echo D | xcopy /s /Y /I %DST_USER_OTHER% %DST_SSH%\administrators_authorized_keys

)
REM echo D | xcopy /s /Y /I %SRC_SSH%\sshd_config %DST_SSH%\sshd_config
powershell.exe "Set-Service ssh-agent -StartupType automatic"
powershell.exe "Start-Service ssh-agent"
powershell.exe "Set-Service sshd -StartupType automatic"
powershell.exe "Start-Service sshd"
netsh advfirewall firewall add rule name="Allow SSH (Port 22)" dir=in action=allow protocol=TCP localport=22

endlocal


