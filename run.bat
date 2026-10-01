@echo off
REM Starts the CrimsonCart Receipts IDOR lab on Windows.
REM No dependencies required - Python 3 standard library only.
cd /d "%~dp0"
python server.py
if errorlevel 1 (
    py -3 server.py
)
pause
