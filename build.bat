@echo off
echo =====================================
echo   Building Draft Assistant .exe
echo =====================================

python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install "pyinstaller>=6.0"
    if errorlevel 1 (
        echo ERROR: failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo.
echo [1/3] Cleaning old builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo [2/3] Checking icon...
if not exist "assets\app_icon.ico" (
    python scripts\make_icon.py
)

echo.
echo [3/3] Building .exe ^(takes 1-2 min^)...
pyinstaller build_exe.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo BUILD FAILED
    pause
    exit /b 1
)

echo.
echo =====================================
echo   DONE
echo =====================================
echo File: dist\DraftAssistant.exe
echo.
choice /c YN /m "Open app now"
if errorlevel 2 goto :end
start "" "dist\DraftAssistant.exe"
:end
