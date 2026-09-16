@echo off
rem VoiceDeck — запуск интерфейса: сервер + браузер. Окно не закрывать.
cd /d "%~dp0"
python scripts\app.py
pause
