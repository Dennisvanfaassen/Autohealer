@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run setup.bat first.
 pause
 exit /b 1
)
REM Change only this path if your SoulBound client is elsewhere.
set "SOULBOUND_PATCHER=C:\Soulbound_Journey_Client\Soulbound_Journey_Client\Soulbound.exe"
".venv\Scripts\python.exe" autohealer.py --patcher "%SOULBOUND_PATCHER%" --item "Meat" --min-hp 13 --max-hp 16 --burst-min 1 --burst-max 3
pause
