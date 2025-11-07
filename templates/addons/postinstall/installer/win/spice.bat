
echo off
setlocal

:: Read env config
call D:\umi\config\env.bat
set "SRC_SSH=D:\umi\ssh\"
set "SPICE_TOOLS=https://www.spice-space.org/download/windows/spice-guest-tools/spice-guest-tools-latest.exe"
set "SPICE_WEBDAV=https://www.spice-space.org/download/windows/spice-webdavd/spice-webdavd-x64-2.4.msi"
set "INSTALLER_TOOLS=%TEMP%\spice-guest-tools-latest.exe"
set "INSTALLER_WEBDAV=%TEMP%\spice-webdavd-x64-2.4.msi"

:: Install tools
curl -L -o %INSTALLER_TOOLS% %SPICE_TOOLS%
curl -L -o %INSTALLER_WEBDAV% %SPICE_WEBDAV%

%INSTALLER_TOOLS% /S
msiexec /package %INSTALLER_WEBDAV% /passive

endlocal



