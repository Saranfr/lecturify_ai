@echo off
REM Run Lecturify backend - ensures venv is used
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo Using venv: %VIRTUAL_ENV%
)
echo Installing dependencies...
python -m pip install python-pptx python-docx PyMuPDF olefile imageio-ffmpeg openai-whisper moviepy av -q
if errorlevel 1 (
    echo WARNING: Some packages may have failed. Check above.
)
echo.
echo Starting backend...
python run_backend.py
