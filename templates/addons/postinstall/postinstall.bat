
echo off
setlocal

:: Read env config
call D:\umi\config\env.bat

:: Essentials
call D:\umi\postinstall\installer\win\user.bat
call D:\umi\postinstall\installer\win\essentials.bat
call D:\umi\postinstall\installer\win\ssh.bat
call D:\umi\postinstall\installer\win\debug.bat
call D:\umi\postinstall\installer\win\spice.bat
call D:\umi\postinstall\installer\win\titus.bat
REM call D:\umi\postinstall\installer\win\cloudbase.bat
REM call D:\umi\postinstall\installer\win\finalize.bat

endlocal


