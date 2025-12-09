@echo off
echo 🚀 Starting OmniVid Lite with Frontend and Backend
echo ===================================================

echo 📦 Installing backend dependencies (if needed)...
where python >nul 2>nul
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

if not exist ".venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv .venv
)

echo 🔧 Activating virtual environment and installing requirements...
call .venv\Scripts\activate.bat
pip install -r requirements.txt

echo 🌟 Starting FastAPI backend on port 8000...
start "OmniVid Backend" cmd /k "cd /d %~dp0.. && .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo 🎨 Installing and starting React frontend on port 3000...
if not exist "frontend\node_modules" (
    echo 📦 Installing frontend dependencies...
    cd frontend
    npm install
    cd ..
)

start "OmniVid Frontend" cmd /k "cd /d %~dp0..\frontend && npm start"

timeout /t 2 /nobreak >nul

echo ✅ Services starting up!
echo.
echo 🌐 Frontend: http://localhost:3000
echo 🚀 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo 💡 Tips:
echo    - Close both command windows to stop services
echo    - Check browser developer tools for any frontend errors
echo    - Use 'test_video_direct.py' for direct testing without frontend
echo.
echo 🎬 Ready to generate videos from prompts!
echo Press any key to close this window...
pause >nul
