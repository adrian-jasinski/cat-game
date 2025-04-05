@echo off
echo Setting up Cat Platformer Game...

:: Check if Python 3.12 is installed
python check_python_version.py
if %ERRORLEVEL% neq 0 (
    pause
    exit /b 1
)

:: Check for uv
uv --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo uv is not installed. Please install uv manually from https://github.com/astral-sh/uv
    echo You can also use the alternate pip setup described in README.md
    pause
    exit /b 1
)

:: Create virtual environment with Python 3.12
echo Creating virtual environment with Python 3.12...
uv venv --python=python3.12

:: Install dependencies
echo Installing dependencies...
call .venv\Scripts\activate.bat
uv pip install -e .

echo.
echo Setup complete! You can now run the game with: python cat_platformer_game.py
echo To activate the environment in the future, run: .venv\Scripts\activate.bat
pause 