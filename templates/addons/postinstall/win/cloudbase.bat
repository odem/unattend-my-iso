
echo off
setlocal

:: Read env config
call D:\umi\config\env.bat

:: Define variables
set "URL_CB=https://github.com/cloudbase/cloudbase-init/releases/download/1.1.6/CloudbaseInitSetup_1_1_6_x64.msi"
set "INSTALLER_CB=%TEMP%\cloudbase.msi"

:: Install Cloudbase
curl -o %INSTALLER_CB% %URL_CB%
msiexec /package %INSTALLER_CB% /passive
del "%INSTALLER_CB%"
echo Cloudbase installed successfully

:: Install Cloudbase

endlocal


