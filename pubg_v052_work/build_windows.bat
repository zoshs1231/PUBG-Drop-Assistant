@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
 echo Python launcher not found. Install Python 3.11 or 3.12 with py launcher.
 pause
 exit /b 1
)
py -3 -m venv .venv
if errorlevel 1 exit /b 1
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python -m PyInstaller --noconfirm --clean --onefile --windowed --name PUBG_Drop_Assistant --collect-all cv2 --collect-all truststore --collect-data certifi app.py
if errorlevel 1 exit /b 1
echo.
echo EXE ready: dist\PUBG_Drop_Assistant.exe
pause
