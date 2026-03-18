@echo off
echo ============================================
echo   Building AI-Transcriber.exe ...
echo ============================================
echo.

pyinstaller main.spec --noconfirm

echo.
if exist "dist\AI-Transcriber.exe" (
    echo  BUILD SUCCESSFUL!
    echo  Output: dist\AI-Transcriber.exe
) else (
    echo  BUILD FAILED — check the output above for errors.
)
echo.
pause
