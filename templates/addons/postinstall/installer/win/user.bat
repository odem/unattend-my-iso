
echo off
setlocal

:: Read env config
call D:\umi\config\env.bat
set "SRC_USER_OTHER=D:\umi\users\%CFG_USER_OTHER_NAME%"
set "DST_USER_OTHER=C:\Users\%CFG_USER_OTHER_NAME%"
set "DST_WALLPAPER=C:\Users\%CFG_USER_OTHER_NAME%\wallpaper.jpg"
xcopy /E /Y /H /K /R %SRC_USER_OTHER%\* %DST_USER_OTHER%

:: Set Wallpaper
reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v Wallpaper /t REG_SZ /d %DST_WALLPAPER% /f
reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v WallpaperStyle /t REG_SZ /d 10 /f
reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v TileWallpaper /t REG_SZ /d 0 /f
RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters 

endlocal


