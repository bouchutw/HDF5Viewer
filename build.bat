@echo off
REM Build the application using PyInstaller
pyinstaller --onefile --noconsole --icon=resources/icon.ico main.py

REM Notify completion
echo Build completed! The executable is in the "dist" folder.
pause
