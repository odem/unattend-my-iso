
echo off
setlocal

:: Read env config
call D:\umi\config\env.bat

:: Define variables
set "URL_CB=https://github.com/cloudbase/cloudbase-init/releases/download/1.1.6/CloudbaseInitSetup_1_1_6_x64.msi"
set "INSTALLER_CB=%TEMP%\cloudbase.msi"
set "SRC_CONFIG_CB=D:/umi/postinstall/cloudinit"
set "DST_CONFIG_CB=C:\Program Files\Cloudbase Solutions\Cloudbase-Init\conf"

:: Install Cloudbase
curl -L -o %INSTALLER_CB% %URL_CB%
msiexec /package %INSTALLER_CB% /passive
del "%INSTALLER_CB%"
xcopy /E /Y /H /K /R %SRC_CONFIG_CB%\* %DST_CONFIG_CB%
echo Cloudbase installed successfully


:: Install Cloudbase

endlocal


