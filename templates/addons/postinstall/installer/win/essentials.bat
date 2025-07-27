
echo off
setlocal

:: Read env config
call D:\umi\config\env.bat

:: Define variables
set "URL_7ZIP=https://7-zip.org/a/7z2500-x64.msi"
set "INSTALLER_7ZIP=%TEMP%\7zip_installer.exe"

:: Install Guest-Utils
D:\umi\virtio\virtio_win_guest_tools.exe /install /passive /quite /norestart
echo Guest utils installed successfully

:: Install 7zip
curl -o %INSTALLER_7ZIP% %URL_7ZIP%
msiexec /package %INSTALLER_7ZIP% /passive
del "%INSTALLER_7ZIP%"
echo 7-Zip installed successfully

endlocal


