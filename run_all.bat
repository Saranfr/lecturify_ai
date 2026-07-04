@echo off
REM Start Lecturify AI - Backend + Frontend together
cd /d "%~dp0"

echo Starting Lecturify AI...
echo.

REM Start backend in a new window
start "Lecturify Backend" cmd /k "cd /d %~dp0 && start_backend.bat"

REM Wait 3 seconds for backend to initialize
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
start "Lecturify Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both backend and frontend are starting in separate windows.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Open http://localhost:5173 in your browser.
pause
