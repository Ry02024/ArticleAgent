@echo off
echo Creating virtual environment...
python -m venv .venv

echo Activating virtual environment and installing dependencies...
call .venv\Scripts\activate
pip install -r requirements.txt

echo.
echo Setup complete!
echo To activate the virtual environment, run: .venv\Scripts\activate
pause
