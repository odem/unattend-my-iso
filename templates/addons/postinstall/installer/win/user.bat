
echo off
setlocal

:: Read env config
call D:\umi\config\env.bat
set "SRC_USER_OTHER=D:\umi\users\%CFG_USER_OTHER_NAME%\"
set "DST_USER_OTHER=C:\Users\%CFG_USER_OTHER_NAME%\"
set "SRC_IMAGE_FH=D:\umi\users\%CFG_USER_OTHER_NAME%\wallpaper.jpg"
set "DST_IMAGE_FH=C:\Users\%CFG_USER_OTHER_NAME%\wallpaper.jpg"
echo "J" | xcopy /s /Y /I %SRC_USER_OTHER% %DST_IMAGE_FH%

:: Set Wallpaper
REM echo D | xcopy /s /Y /I %SRC_IMAGE_FH% %DST_USER_OTHER%
reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v Wallpaper /t REG_SZ /d %DST_IMAGE_FH% /f
reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v WallpaperStyle /t REG_SZ /d 10 /f
reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v TileWallpaper /t REG_SZ /d 0 /f
RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters 

endlocal


