@echo off
rem Asgard Theme Studio - Created November 22, 2026 by The_Mead_Maker & Odin. Copyright (c) 2026 The_Mead_Maker & Odin. MIT License.
rem Builds dist\Asgard Theme Studio\Asgard Theme Studio.exe (PyInstaller, one folder, no console) and, if Inno Setup 6 is
rem found, Output\Asgard-Theme-Studio-Setup-<ver>.exe. Same approach as Asgard.exe and Valhalla.exe. Standard library only.
setlocal
cd /d %~dp0..
set VER=1.0.0
if not exist venv py -3.12 -m venv venv || py -3 -m venv venv || exit /b 1
venv\Scripts\python -m pip install -q --disable-pip-version-check pyinstaller || exit /b 1
venv\Scripts\python tests\test_theme_check.py || exit /b 1
venv\Scripts\python -m PyInstaller --noconfirm --clean --onedir --windowed --name "Asgard Theme Studio" --icon windows\studio.ico --contents-directory . ^
  --version-file windows\version_info.txt ^
  --add-data "static;static" --add-data "themes;themes" --add-data "docs;docs" --add-data "windows\studio.ico;." ^
  --add-data "LICENSE;." --add-data "README.md;." --add-data "CHANGELOG.md;." --add-data "CREDITS.txt;." ^
  --hidden-import theme_check --paths . studio_app.py || exit /b 1
venv\Scripts\python windows\release_check.py "dist\Asgard Theme Studio" || exit /b 1
set ISCC=
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%~dp0..\innosetup\ISCC.exe" set ISCC="%~dp0..\innosetup\ISCC.exe"
if exist "%~dp0..\..\asgard-exe-build\innosetup\ISCC.exe" set ISCC="%~dp0..\..\asgard-exe-build\innosetup\ISCC.exe"
if not defined ISCC (echo Inno Setup 6 not found; skipped the installer. & exit /b 0)
%ISCC% /Q /DAppVer=%VER% windows\studio.iss || exit /b 1
echo Installer: %CD%\Output
