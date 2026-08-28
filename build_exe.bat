@echo off
chcp 65001 >nul
echo Building CodePlot Windows executable...

REM Install pyinstaller if missing
python -m pip install pyinstaller numpy matplotlib pillow --quiet 2>nul

REM Generate icon if missing
if not exist icon.ico python make_icon.py

REM Clean previous build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build: onedir, windowed (no console), include compose engine, use emoji icon
python -m PyInstaller ^
  --name CodePlot ^
  --windowed ^
  --onedir ^
  --clean ^
  --noconfirm ^
  --icon icon.ico ^
  --hidden-import compose_figure ^
  --hidden-import numpy ^
  --hidden-import PIL ^
  --hidden-import PIL.ImageTk ^
  --add-data "compose_figure.py;." ^
  --add-data "compose_settings.json;." ^
  codeplot.py

if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo Build complete: dist/CodePlot/CodePlot.exe
echo.
pause
