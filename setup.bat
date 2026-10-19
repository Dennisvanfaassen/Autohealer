@echo off
setlocal
cd /d "%~dp0"
where git >nul 2>&1
if errorlevel 1 (
 echo Git is required. Install Git for Windows and retry.
 pause
 exit /b 1
)
if not exist "vendor\Ragnarok\diagnostics\authenticated_client.py" (
 git clone --depth 1 https://github.com/Dennisvanfaassen/Ragnarok.git vendor\Ragnarok
 if errorlevel 1 (echo Could not download original bot backend.& pause & exit /b 1)
)
if not exist ".venv\Scripts\python.exe" (
 py -3 -m venv .venv
 if errorlevel 1 (echo Python 3 is required.& pause & exit /b 1)
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r "vendor\Ragnarok\requirements.txt"
if errorlevel 1 (echo Dependency installation failed.& pause & exit /b 1)
echo Setup complete. Edit run.bat to set your SoulBound.exe location.
pause
