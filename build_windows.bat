
@echo off
pip install -r requirements.txt
pyinstaller --onefile --windowed --name ERPParaguay main.py
pause
