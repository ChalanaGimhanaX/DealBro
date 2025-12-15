@echo off
REM Start script for DealBro backend services (Windows)

echo ================================
echo Starting DealBro Backend
echo ================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Error: Virtual environment not found
    echo Please run setup.py first
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo Error: .env file not found
    echo Please copy .env.example to .env and configure it
    exit /b 1
)

echo.
echo Starting API server on port 8000...
start "DealBro API" python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

echo.
echo API server started
echo.
echo To start the ingestion scheduler, run:
echo   python -m app.ingestion.scheduler
echo.
echo Press any key to exit...
pause > nul
